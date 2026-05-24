from typing import List
from backend.intelligence.cdl.schema import SymbolContract, ContractDelta, BreakingChangeType

class ContractDiffer:
    """
    Compares two SymbolContracts and returns a ContractDelta.
    Logic is deterministic.
    """
    def diff(self, old: SymbolContract, new: SymbolContract) -> ContractDelta:
        changes = []
        is_breaking = False

        # 1. Parameter changes
        old_params = {p['name']: p for p in old.parameters}
        new_params = {p['name']: p for p in new.parameters}

        # Check for removed parameters
        for name in old_params:
            if name not in new_params:
                changes.append(BreakingChangeType.PARAM_REMOVED)
                is_breaking = True

        # Check for added parameters
        for name, p in new_params.items():
            if name not in old_params:
                if p.get('required', True) and p.get('default') is None:
                    changes.append(BreakingChangeType.PARAM_ADDED_REQUIRED)
                    is_breaking = True

        # 2. Return type changes
        if old.return_type != new.return_type:
            # Simplistic check: any change is flagged
            # A more advanced version would handle type hierarchy
            changes.append(BreakingChangeType.RETURN_TYPE_CHANGED)
            is_breaking = True

        # 3. Async changes
        if old.is_async != new.is_async:
            changes.append(BreakingChangeType.ASYNC_CHANGED)
            is_breaking = True

        # 4. Visibility changes
        visibility_order = {"public": 3, "protected": 2, "private": 1}
        if visibility_order.get(new.visibility, 0) < visibility_order.get(old.visibility, 0):
            changes.append(BreakingChangeType.VISIBILITY_REDUCED)
            is_breaking = True

        # 5. Exceptions added
        old_raises = set(old.raises)
        for ex in new.raises:
            if ex not in old_raises:
                changes.append(BreakingChangeType.EXCEPTION_ADDED)
                is_breaking = True

        semver = self.suggest_semver(is_breaking, changes)

        return ContractDelta(
            symbol=new.qualified_name,
            changes=changes,
            old_contract=old,
            new_contract=new,
            is_breaking=is_breaking,
            semver_suggestion=semver
        )

    def suggest_semver(self, is_breaking: bool, changes: List[BreakingChangeType]) -> str:
        if is_breaking:
            return "major"
        if changes:
            return "minor"
        return "patch"

contract_differ = ContractDiffer()
