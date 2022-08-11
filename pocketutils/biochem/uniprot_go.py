import dataclasses
import logging
import os
from dataclasses import dataclass
from typing import Collection, Iterable, List, Mapping, Optional, Union
from urllib import request

import pandas as pd
import regex
import uniprot

# uses https://github.com/tanghaibao/goatools
from goatools import obo_parser

# NOT the same as FlatGoTerm, which has no knowledge of hierarchy
from goatools.obo_parser import GOTerm

from pocketutils.core.exceptions import MultipleMatchesError, StringPatternError

# noinspection PyProtectedMember
from pocketutils.core.input_output import silenced

go_pattern = regex.compile(
    r"GO:(\d+); ([CFP]):([\dA-Za-z- ,()]+); ([A-Z]+):([A-Za-z-_]+)\.", flags=regex.V1
)
GO_OBO_URL = "http://current.geneontology.org/ontology/go.obo"  # nosec
GO_OBO_FILENAME = "go.obo"
logger = logging.getLogger("pocketutils")


@dataclass(frozen=True, repr=True)
class FlatGoTerm:
    """
    A Gene Ontology term.
    Not to be confused with GOTerm in goatools: obo_parser.GOTerm

    Attributes:
        - identifier: (str); ex: GO:0005737
        - kind: (str: 'P'==process, 'C'==component, 'F'==function)
        - description: (str)
        - sourceId: (str); ex: IDA
        - sourceName: (str); ex: UniProtKB
    """

    identifier: str
    kind: str
    description: str
    source_id: str
    source_name: str

    @classmethod
    def parse(cls, stwing: str):
        """
        Builds a GO term from a string from uniprot_obj['go'].
        Raises:
            ValueError: if the syntax is wrong.
        """
        match = go_pattern.search(stwing)
        if match is None:
            raise StringPatternError(
                f"String didn't match GO term pattern: {stwing}",
                value=stwing,
                pattern=go_pattern,
            )
        return FlatGoTerm(
            "GO:" + match.group(1),
            match.group(2),
            match.group(3),
            match.group(4),
            match.group(5),
        )

    def to_series(self) -> pd.Series:
        return pd.Series(dataclasses.asdict(self))


class UniprotGoTerms:
    def fetch_uniprot_data(self, uniprot_ids: Union[str, List[str]]) -> List[Mapping[str, str]]:
        """
        Fetches a list of dicts of UniProt metadata, one per UniProt ID.

        Raises:
            ValueError: If a UniProt ID wasn't found.
        """
        if isinstance(uniprot_ids, str):  # not a list type
            uniprot_ids = [uniprot_ids]
        # if we don't prevent these here, we'll get a ValueError from below, which is confusing
        # That's because uniprot.fetch_uniprot_metadata will only return one per unique ID
        if len(set(uniprot_ids)) != len(uniprot_ids):
            raise MultipleMatchesError("Set of UniProt IDs cannot contain duplicates")
        with silenced(no_stderr=False):
            uniprot_data = uniprot.fetch_uniprot_metadata(uniprot_ids)
        if uniprot_data is None or uniprot_data == {} or len(uniprot_data) != len(uniprot_ids):
            raise LookupError(f"At least one UniProt ID not found in {uniprot_ids}")
        return list(uniprot_data.values())

    def go_terms_for_uniprot_id(self, uniprot_id: str) -> List[FlatGoTerm]:
        """Returns a list of FlatGoTerm objects from a UniProt ID."""
        term_strings = (self.fetch_uniprot_data(uniprot_id)[0])["go"]
        return [FlatGoTerm(s) for s in term_strings]

    def go_terms_for_uniprot_id_as_df(self, uniprot_id: str) -> pd.DataFrame:
        """Returns a Pandas DataFrame of GO terms from a UniProt ID."""
        df = pd.DataFrame(columns=["ID", "kind", "description", "sourceId", "sourceName"])
        for term in self.go_terms_for_uniprot_id(uniprot_id):
            df.loc[len(df)] = term.to_series()
        return df.set_index("ID")


class GoTermsAtLevel:
    """
    Gene ontology terms organized by level.

    Example:
        .. code-block::

            go_term_ancestors_for_uniprot_id_as_df('P42681', 2)
    """

    def __init__(self) -> None:
        if os.path.exists(GO_OBO_FILENAME):
            self.obo = obo_parser.GODag(GO_OBO_FILENAME)
        else:
            logger.info("Downloading Gene Ontology OBO...")
            request.urlretrieve(GO_OBO_URL)  # nosec
            # This will be used in query_obo_term
            self.obo = obo_parser.GODag(GO_OBO_FILENAME)
            logger.info("Done downloading OBO.")
        self.substruct = UniprotGoTerms()

    def query_obo_term(self, term_id: str) -> GOTerm:
        """
        Queries a term through the global obo.
        This function wraps the call to raise a ValueError if the term is not found;
        otherwise it only logs a warning.
        """
        x = self.obo.query_term(term_id)
        if x is None:
            raise LookupError(f"Term ID {x} not found")
        return x

    def get_ancestors_of_go_term(self, term_id: str, level: int) -> Iterable[GOTerm]:
        """
        From a GO term in the form 'GO:0007344', returns a set of ancestor GOTerm objects at the specified level.
        The traversal is restricted to is-a relationships.
        Note that the level is the minimum number of steps to the root.

        Args:
            term_id: The term
            level: starting at 0 (root)
        """

        def traverse_up(term, buildup_set, lvl):
            if term.level == lvl:
                buildup_set.add(term)
            if term.has_parent:
                return [traverse_up(p, buildup_set, lvl) for p in term.parents]
            return None

        terms = set()
        traverse_up(self.query_obo_term(term_id), terms, level)
        return terms

    def go_term_ancestors_for_uniprot_id(
        self, uniprot_id: str, level: int, kinds_allowed: Optional[Collection[str]] = None
    ) -> Iterable[GOTerm]:
        """
        Gets the GO terms associated with a UniProt ID and returns a set of their ancestors at the specified level.
        The traversal is restricted to is-a relationships.
        Note that the level is the minimum number of steps to the root.

        Args:
            level: starting at 0 (root)
            uniprot_id: ID
            kinds_allowed: a set containing any combination of 'P', 'F', or 'C'
        """
        if kinds_allowed is None:
            kinds_allowed = ["P", "F", "C"]
        if len(kinds_allowed) == 0:
            return []
        terms = [
            term
            for term in self.substruct.go_terms_for_uniprot_id(uniprot_id)
            if term.kind in kinds_allowed
        ]
        ancestor_terms = set()
        for term_id in [t.identifier for t in terms]:
            ancestor_terms.update(self.get_ancestors_of_go_term(term_id, level))
        return ancestor_terms

    def go_term_ancestors_for_uniprot_id_as_df(
        self, uniprot_id: str, level: int, kinds_allowed: Optional[Collection[str]] = None
    ) -> pd.DataFrame:
        """
        See go_term_ancestors_for_uniprot_id.

        Args:
            uniprot_id: ID
            level: Level
            kinds_allowed: Can include 'P', 'F', and/or 'C'

        Returns:
             Pandas DataFrame with columns IDand name.
        """
        if kinds_allowed is None:
            kinds_allowed = ["P", "F", "C"]
        df = pd.DataFrame(columns=["ID", "name"])
        for term in self.go_term_ancestors_for_uniprot_id(uniprot_id, level, kinds_allowed):
            df.loc[len(df)] = pd.Series({"ID": term.id, "name": term.name, "level": term.level})
        return df.set_index("ID")


__all__ = ["FlatGoTerm", "UniprotGoTerms", "GoTermsAtLevel"]
