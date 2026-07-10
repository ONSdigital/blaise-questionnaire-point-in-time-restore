from datetime import datetime

from models.database_clone_model import DatabaseCloneModel


def test_database_clone_model_allows_expected_attributes() -> None:
    model = DatabaseCloneModel()
    now = datetime(2026, 7, 10, 12, 0, 0)

    model.source_instance_name = "source-instance"
    model.destination_instance_name = "destination-instance"
    model.point_in_time = now

    assert model.source_instance_name == "source-instance"
    assert model.destination_instance_name == "destination-instance"
    assert model.point_in_time == now
