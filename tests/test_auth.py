import random
import pytest


@pytest.mark.asyncio
class TestRegister:
    async def test_register_success(self, client):
        test_user = f"test_user_{random.randint(1, 9999999)}"
        response_success = await client.post("/auth/register",
                                             json={
                                                 "name": test_user,
                                                 "password": "secret",
                                                 "email": f"{test_user}@gmail.com",
                                             })
        assert response_success.status_code == 201
        assert response_success.json() == {"ok": True}

    @pytest.mark.parametrize("first_username,first_email,second_username, second_email, detail_text",
                             [
                                 ("test_user_123", "test_user_123@gmail.com", "test_user_123", "another@gmail.com",
                                  "Username taken"),
                                 ("test_user_321", "test_user_321@gmail.com", "another", "test_user_321@gmail.com",
                                  "Email already registered")
                             ])
    async def test_register_duplicates(self, first_username, first_email, second_username, second_email, detail_text,
                                       client):
        response_success = await client.post("/auth/register",
                                             json={
                                                 "name": first_username,
                                                 "password": "secret",
                                                 "email": first_email,
                                             })
        assert response_success.status_code == 201

        response_duplicate = await client.post("/auth/register",
                                               json={
                                                   "name": second_username,
                                                   "password": "secret",
                                                   "email": second_email,
                                               })
        assert response_duplicate.status_code == 400
        assert response_duplicate.json()["detail"] == detail_text


@pytest.mark.asyncio
class TestLogin:
    async def test_login_success(self, client):
        await client.post("/auth/register",
                          json={
                              "name": "test_user_for_login",
                              "password": "secret",
                              "email": f"test_user_for_login@gmail.com",
                          })
        response = await client.post("/auth/login", data={
            "username": "test_user_for_login",
            "password": "secret"
        })
        assert response.status_code == 201
        assert response.json()["access_token"] is not None

    @pytest.mark.parametrize("username_create,password_create,username_login,password_login", [
        ("test_user_1", "secret", "test_user_9999", "secret"),
        ("test_user_2", "secret", "test_user_2", "password"),
        ("test_user_3", "secret", "test_user_another", "another")
    ])
    async def test_login_failure(self, username_create, password_create, username_login,
                                 password_login, client):
        await client.post("/auth/register",
                          json={
                              "name": username_create,
                              "password": password_create,
                              "email": f"{username_create}@gmail.com",
                          })
        response = await client.post("/auth/login", data={
            "username": username_login,
            "password": password_login
        })
        assert response.status_code == 400


@pytest.mark.asyncio
class TestAuthMe:

    async def test_auth_me_success(self, client, auth_header):
        response_success = await client.get("/auth/me", headers=auth_header)
        assert response_success.status_code == 200
        assert response_success.json()['name'] == 'test_user_auth'

    async def test_auth_me_failure(self, client):
        response_failure = await client.get("/auth/me")
        assert response_failure.status_code == 401
