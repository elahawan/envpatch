"""Compare two .env files and produce a structured summary of key coverage."""

from dataclasses import dataclass, field
from typing import List, Set

from envpatch.parser import EnvFile


@dataclass
class CoverageReport:
    """Summary of key coverage between a reference and target .env file."""

    reference_path: str
    target_path: str
    common_keys: Set[str] = field(default_factory=set)
    only_in_reference: Set[str] = field(default_factory=set)
    only_in_target: Set[str] = field(default_factory=set)

    @property
    def coverage_ratio(self) -> float:
        """Fraction of reference keys present in target (0.0 – 1.0)."""
        total = len(self.only_in_reference) + len(self.common_keys)
        if total == 0:
            return 1.0
        return len(self.common_keys) / total

    @property
    def missing_keys(self) -> List[str]:
        """Sorted list of keys in reference but absent from target."""
        return sorted(self.only_in_reference)

    @property
    def extra_keys(self) -> List[str]:
        """Sorted list of keys in target but absent from reference."""
        return sorted(self.only_in_target)

    def is_complete(self) -> bool:
        """Return True when target contains every key from reference."""
        return len(self.only_in_reference) == 0


def compare_coverage(reference: EnvFile, target: EnvFile,
                     reference_path: str = "",
                     target_path: str = "") -> CoverageReport:
    """Compare *target* against *reference* and return a CoverageReport.

    Args:
        reference: The authoritative .env file (e.g. .env.example).
        target:    The file being checked (e.g. .env.production).
        reference_path: Display path for the reference file.
        target_path:    Display path for the target file.

    Returns:
        A :class:`CoverageReport` instance.
    """
    ref_keys: Set[str] = {
        e.key for e in reference.entries if e.key is not None
    }
    tgt_keys: Set[str] = {
        e.key for e in target.entries if e.key is not None
    }

    return CoverageReport(
        reference_path=reference_path,
        target_path=target_path,
        common_keys=ref_keys & tgt_keys,
        only_in_reference=ref_keys - tgt_keys,
        only_in_target=tgt_keys - ref_keys,
    )
