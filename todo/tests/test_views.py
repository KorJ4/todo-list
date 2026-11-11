from django.test import TestCase
from django.urls import reverse

from todo.models import Tag, Task

HOME_URL = reverse("todo:task-list")


class TaskViewsTests(TestCase):
    def test_tasks_ordered_not_done_first_then_newest(self) -> None:
        old = Task.objects.create(content="Old")
        done = Task.objects.create(content="Done", is_done=True)
        new = Task.objects.create(content="New")
        response = self.client.get(HOME_URL)
        self.assertEqual(list(response.context["task_list"]), [new, old, done])

    def test_home_shows_task_info_and_buttons(self) -> None:
        task = Task.objects.create(content="Buy milk")
        task.tags.add(Tag.objects.create(name="shop"))
        response = self.client.get(HOME_URL)
        for text in ("Buy milk", "shop", "Complete", "Update", "Delete"):
            with self.subTest(text=text):
                self.assertContains(response, text)

    def test_toggle_status_and_redirect(self) -> None:
        task = Task.objects.create(content="Toggle")
        url = reverse("todo:task-toggle-status", args=[task.pk])
        response = self.client.post(url)
        self.assertRedirects(response, HOME_URL)
        task.refresh_from_db()
        self.assertTrue(task.is_done)
        self.client.post(url)
        task.refresh_from_db()
        self.assertFalse(task.is_done)

    def test_toggle_rejects_get(self) -> None:
        task = Task.objects.create(content="Safe")
        url = reverse("todo:task-toggle-status", args=[task.pk])
        self.assertEqual(self.client.get(url).status_code, 405)

    def test_create_task_with_tags(self) -> None:
        tag = Tag.objects.create(name="work")
        response = self.client.post(
            reverse("todo:task-create"),
            {"content": "Write report", "tags": [tag.pk]},
        )
        self.assertRedirects(response, HOME_URL)
        task = Task.objects.get(content="Write report")
        self.assertIsNone(task.deadline)
        self.assertEqual(list(task.tags.all()), [tag])


class TagViewsTests(TestCase):
    def test_tag_list(self) -> None:
        Tag.objects.create(name="home")
        response = self.client.get(reverse("todo:tag-list"))
        self.assertContains(response, "home")

    def test_tag_crud(self) -> None:
        self.client.post(reverse("todo:tag-create"), {"name": "hobby"})
        tag = Tag.objects.get(name="hobby")
        self.client.post(
            reverse("todo:tag-update", args=[tag.pk]), {"name": "sport"}
        )
        tag.refresh_from_db()
        self.assertEqual(tag.name, "sport")
        response = self.client.post(reverse("todo:tag-delete", args=[tag.pk]))
        self.assertRedirects(response, reverse("todo:tag-list"))
        self.assertFalse(Tag.objects.exists())
