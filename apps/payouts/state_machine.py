LEGAL_TRANSITIONS = {
    'pending': ['processing'],
    'processing': ['completed', 'failed'],
}

class IllegalTransitionError(Exception):
    pass

def transition(payout, to_state: str):
    """
    Only place in the codebase that writes payout.status.
    Raises if transition is illegal.
    Does NOT save — caller must call payout.save() inside their transaction.
    """
    allowed = LEGAL_TRANSITIONS.get(payout.status, [])
    if to_state not in allowed:
        raise IllegalTransitionError(
            f'Transition {payout.status} → {to_state} is not allowed'
        )
    payout.status = to_state