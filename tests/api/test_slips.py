def test_post_and_get_slips(client):
    first = client.post("/slips", json={"occurred_on": "2026-08-10"})
    second = client.post("/slips", json={"occurred_on": "2026-08-11", "note": "late"})
    assert first.status_code == 201, first.text
    assert second.json()["metric"] == "slip"
    assert second.json()["value_num"] == 1.0
    assert second.json()["source"] == "api"

    view = client.get("/slips", params={"as_of": "2026-08-14"})
    assert view.status_code == 200, view.text
    body = view.json()
    assert body["this_week"] == 2.0
    assert body["series"][0] == 1.0
    assert body["series"][1] == 1.0
