from datetime import datetime, timezone, timedelta, UTC
import pytest


@pytest.mark.asyncio
class TestTaskCreate:
    @pytest.mark.parametrize(
        "title,description,priority,is_done,due_date", [
            ("test_task 1", "", 2, False, "2029-09-09T09:09:09.009Z"),
            ("test_task 2", "test_description", 4, True, "2028-08-08T08:08:08.008Z"),
        ]
    )
    async def test_create_task_valid(self, title, description, priority, is_done, due_date, client, auth_header):
        task_response = await client.post("/tasks", json={
            "title": title,
            "description": description,
            "priority": priority,
            "is_done": is_done,
            "due_date": due_date
        }, headers=auth_header)
        assert task_response.status_code == 201
        assert "id" in task_response.json().keys()

    @pytest.mark.parametrize(
        "title,description,priority,is_done,due_date", [
            ("test_task_1", "", 5, False, "2029-09-09T09:09:09.009Z"),
            ("", "test_description", 4, True, "2028-08-08T08:08:08.008Z"),
            ("invalid date", "test_description", 1, True, "2028-13-08T08:08:08.008Z"),
            (f"{str(pow(9999999999999, 9))}", "test_description", 3, True, "2025-08-08T08:08:08.008Z"),
        ]
    )
    async def test_create_task_invalid(self, title, description, priority, is_done, due_date, client, auth_header):
        task_response = await client.post("/tasks", json={
            "title": title,
            "description": description,
            "priority": priority,
            "is_done": is_done,
            "due_date": due_date
        }, headers=auth_header)
        assert task_response.status_code == 422

    async def test_create_task_duplicate(self, client, auth_header):
        await client.post("/tasks", json={
            "title": "title_duplicate",
            "description": "description",
            "priority": 3,
            "is_done": False,
            "due_date": "2029-09-09T09:09:09.009Z"
        }, headers=auth_header)
        task_response = await client.post("/tasks", json={
            "title": "title_duplicate",
            "description": "description_another",
            "priority": 2,
            "is_done": True,
            "due_date": "2028-08-08T08:08:08.008Z"
        }, headers=auth_header)
        assert task_response.status_code == 400


@pytest.mark.asyncio
class TestTaskGet:

    @pytest.fixture(autouse=True)
    async def fill_tasks(self, client, auth_header):
        """Создаёт набор задач для тестирования фильтрации."""
        tasks_data = [
            # is_done=False, not overdue, priority=1
            {"title": "Task 1", "description": "desc1", "priority": 1, "is_done": False,
             "due_date": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()},
            # is_done=True, overdue (дата в прошлом), priority=2
            {"title": "Task 2", "description": "desc2", "priority": 2, "is_done": True,
             "due_date": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()},
            # is_done=False, not overdue, priority=3
            {"title": "Task 3", "description": "desc3", "priority": 3, "is_done": False,
             "due_date": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()},
            # is_done=True, not overdue, priority=4
            {"title": "Task 4", "description": "desc4", "priority": 4, "is_done": True,
             "due_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()},
            # is_done=False, no due_date, priority=2
            {"title": "Task 5", "description": "desc5", "priority": 2, "is_done": False,
             "due_date": None},
        ]
        for task in tasks_data:
            await client.post("/tasks", json=task, headers=auth_header)

    async def test_get_tasks(self, client, auth_header):
        response = await client.get("/tasks?page=1&limit=10&sort_by=id&order=asc", headers=auth_header)
        assert response.status_code == 200
        result = response.json()
        assert set(result.keys()) == {'items', 'total', 'page', 'limit', 'pages'}
        assert isinstance(result["items"], list)

    async def test_get_big_page(self, client, auth_header):
        response = await client.get("/tasks?page=999&limit=10", headers=auth_header)
        assert response.status_code == 200
        assert response.json()["items"] == []

    @pytest.mark.parametrize("filtering,filtering_value", [
        ("is_done", True),
        ("is_done", False),
        ("overdue", False),
        ("overdue", True),
        ("priority", 1),
        ("priority", 2),
        ("priority", 3),
        ("priority", 4)
    ])
    async def test_get_tasks_filtering(self, filtering, filtering_value, client, auth_header):
        response = await client.get(f"/tasks?page=1&limit=10&sort_by=id&order=asc&{filtering}={filtering_value}",
                                    headers=auth_header)
        list_items = response.json()["items"]
        if filtering == "overdue":
            filter_key, filter_value = "is_done", not filtering_value
        else:
            filter_key, filter_value = filtering, filtering_value
        for item in list_items:
            assert item[filter_key] == filter_value
            if filter_key == "overdue":
                if filtering_value:
                    assert item["due_date"] < datetime.now(UTC)
                else:
                    assert item["due_date"] >= datetime.now(UTC)

    @pytest.mark.parametrize("sort_by,order", [
        ("id", "asc"),
        ("title", "asc"),
        ("priority", "asc"),
        ("due_date", "asc"),
        ("is_done", "asc"),
        ("id", "desc"),
        ("title", "desc"),
        ("priority", "desc"),
        ("due_date", "desc"),
        ("is_done", "desc")
    ])
    async def test_get_tasks_sorting(self, sort_by, order, client, auth_header):
        response = await client.get(f"/tasks?page=1&limit=10&sort_by={sort_by}&order={order}", headers=auth_header)
        list_items = response.json()["items"]
        previous = None
        for item in list_items:
            current = item[sort_by]
            if previous:
                if order == "asc":
                    assert current >= previous
                else:
                    assert current <= previous
            else:
                previous = current


@pytest.mark.asyncio
class TestTaskOperationById:

    @staticmethod
    def create_json_data(title, description, priority, is_done, due_date):
        json_data = dict()
        if title is not None:
            json_data["title"] = title
        if description is not None:
            json_data["description"] = description
        if priority is not None:
            json_data["priority"] = priority
        if is_done is not None:
            json_data["is_done"] = is_done
        if due_date is not None:
            json_data["due_date"] = due_date
        return json_data

    @pytest.fixture(autouse=True)
    async def _setup_tasks(self, client, auth_header):
        """Создаёт задачи для текущего пользователя и для другого."""
        # 1. для test_user_auth
        task1 = await client.post("/tasks", json={
            "title": "My Task 1",
            "description": "Description 1",
            "priority": 1,
            "is_done": False,
            "due_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }, headers=auth_header)
        assert task1.status_code == 201
        self.task_id = task1.json()["id"]

        task2 = await client.post("/tasks", json={
            "title": "My Task 2",
            "description": "Description 2",
            "priority": 2,
            "is_done": False,
            "due_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }, headers=auth_header)
        assert task2.status_code == 201
        self.task_id_2 = task2.json()["id"]

        # 2. Регистрируем второго пользователя и создаём его задачу
        await client.post("/auth/register", json={
            "name": "other_user",
            "password": "secret",
            "email": "other@test.com"
        })
        login = await client.post("/auth/login", data={
            "username": "other_user",
            "password": "secret"
        })
        other_token = login.json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}

        other_task = await client.post("/tasks", json={
            "title": "Other User Task",
            "description": "Other description",
            "priority": 3,
            "is_done": False,
            "due_date": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
        }, headers=other_headers)
        assert other_task.status_code == 201
        self.other_task_id = other_task.json()["id"]

    async def test_get_task(self, client, auth_header):
        response_user = await client.get(f"/tasks/{self.task_id}", headers=auth_header)
        assert response_user.status_code == 200
        assert set(response_user.json().keys()) == {"title", "description", "priority", "is_done", "due_date", "id",
                                                    "created_at", "updated_at", "owner_id"}

    async def test_get_task_another(self, client, auth_header):
        response_another_user = await client.get(f"/tasks/{self.other_task_id}", headers=auth_header)
        assert response_another_user.status_code == 403

    async def test_get_task_not_exist(self, client, auth_header):
        response_another_user = await client.get(f"/tasks/999999", headers=auth_header)
        assert response_another_user.status_code == 404

    @pytest.mark.parametrize(
        "title,description,priority,is_done,due_date,status_code", [
            ("test_task_put", "new_description", 2, False, "2029-09-09T09:09:09.009Z", 200),
            ("My Task 2", "new_description", 2, False, "2029-09-09T09:09:09.009Z", 400),
            (None, "new_description", 2, False, "2029-09-09T09:09:09.009Z", 422),
            ("test_task_put", None, 2, False, "2029-09-09T09:09:09.009Z", 422),
            ("test_task_put", "new_description", 100, False, "2029-09-09T09:09:09.009Z", 422),
        ]
    )
    async def test_put(self, title, description, priority, is_done, due_date, status_code, client, auth_header):
        json_data = self.create_json_data(title, description, priority, is_done, due_date)

        response = await client.put(f"/tasks/{self.task_id}", json=json_data, headers=auth_header)
        assert response.status_code == status_code

    @pytest.mark.parametrize(
        "title,description,priority,is_done,due_date,status_code", [
            ("test_task_put", "new_description", 2, False, "2029-09-09T09:09:09.009Z", 200),
            ("My Task 2", "new_description", 2, False, "2029-09-09T09:09:09.009Z", 400),
            (None, None, 1, None, None, 200),
            ("new_test_task_put", None, 3, True, "2029-10-09T09:09:09.009Z", 200),
            ("test_task_patch", "new_description", 100, False, "2029-09-09T09:09:09.009Z", 422),
        ]
    )
    async def test_patch(self, title, description, priority, is_done, due_date, status_code, client, auth_header):
        json_data = self.create_json_data(title, description, priority, is_done, due_date)

        response = await client.patch(f"/tasks/{self.task_id}", json=json_data, headers=auth_header)
        assert response.status_code == status_code

    async def test_delete_task(self, client, auth_header):
        response_delete_task = await client.delete(f"/tasks/{self.task_id}", headers=auth_header)
        assert response_delete_task.status_code == 204
        response_try_to_get = await client.get(f"/tasks/{self.task_id}", headers=auth_header)
        assert response_try_to_get.status_code == 404

    async def test_delete_task_another(self, client, auth_header):
        response_delete_task = await client.delete(f"/tasks/{self.other_task_id}", headers=auth_header)
        assert response_delete_task.status_code == 403

    async def test_delete_task_not_exist(self, client, auth_header):
        response_delete_task = await client.delete(f"/tasks/999999", headers=auth_header)
        assert response_delete_task.status_code == 404

    async def test_put_another(self, client, auth_header):
        response_put_another_task = await client.put(f"/tasks/{self.other_task_id}", json={
            "title": "Task 123123",
            "description": "test_description",
            "priority": 3,
            "is_done": True,
            "due_date": "2026-07-19T10:10:41.744Z"
        }, headers=auth_header)
        assert response_put_another_task.status_code == 403

    async def test_patch_another(self, client, auth_header):
        response_put_another_task = await client.put(f"/tasks/{self.other_task_id}", json={
            "title": "Task 123123",
            "description": "test_description",
            "priority": 3,
            "is_done": True,
            "due_date": "2026-07-19T10:10:41.744Z"
        }, headers=auth_header)
        assert response_put_another_task.status_code == 403