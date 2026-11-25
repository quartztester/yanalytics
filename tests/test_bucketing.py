from yanalytics.utils import reduce_cpus, reduce_domains_nb, reduce_users_nb


def test_hardware_fields_are_bucketed() -> None:
    # exact system specs would single out rare machines; buckets must not
    assert reduce_cpus(6) == reduce_cpus(7) == 8
    assert reduce_domains_nb(2) == reduce_domains_nb(3) == 4
    assert reduce_users_nb(5) == reduce_users_nb(7) == 8
