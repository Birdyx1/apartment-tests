
def test_tenant_detail(created_tenant, admin_tenant_api):
    tenant_id = created_tenant['id']
    response = admin_tenant_api.detail(tenant_id)
    assert response.status_code == 200
    body = response.json()
    assert body['code'] == 200
    assert body['data']['id'] == tenant_id
    assert body['data']['name'] == created_tenant['name']
    assert body['data']['gender'] == created_tenant['gender']
