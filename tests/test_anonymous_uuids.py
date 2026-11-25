import uuid
from pathlib import Path

from yanalytics_client.main import YanalyticsInstance


def test_per_app_uuids(tmp_path: Path) -> None:
    id_file = str(tmp_path / "analytics-id")
    a = YanalyticsInstance("http://localhost", id_file)
    b = YanalyticsInstance("http://localhost", id_file)

    # deterministic across runs (dedup keeps working)
    assert a.uuid_for("nextcloud") == b.uuid_for("nextcloud")

    # base id is random and never reused as a report uuid
    base = Path(id_file).read_text().strip()
    assert len(base) == len(uuid.uuid4().hex)

    # app / instance / base pseudonyms are all distinct and unrelated
    tags = {"nextcloud", "zabbix", "instance", base}
    assert len({a.uuid_for(t) for t in tags}) == len(tags)
