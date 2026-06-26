def seed(model) -> None:
    if not model.is_seeded():
        model.seed()
