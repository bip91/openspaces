def require_actor(author, agent_name):
    """Une écriture est attribuée à un humain OU à un agent, jamais les deux ni aucun."""
    if bool(author) == bool(agent_name):
        raise ValueError("fournir exactement un de author ou agent_name")
    return ("human", author) if author else ("agent", agent_name)
