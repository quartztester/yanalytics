import uuid
from pathlib import Path

from yanalytics.utils import reduce_cpus, reduce_domains_nb, reduce_users_nb
from yanalytics_client.main import YanalyticsInstance


def test_hardware_fields_are_bucketed() -> None:
    # exact system specs would single out rare machines; buckets must not
    assert reduce_cpus(6) == reduce_cpus(7) == 8
    assert reduce_domains_nb(2) == reduce_domains_nb(3) == 4
    assert reduce_users_nb(5) == reduce_users_nb(7) == 8


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
