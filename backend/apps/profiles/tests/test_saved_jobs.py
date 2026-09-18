import pytest

from apps.applications.models import SavedJob

SAVED = "/api/saved-jobs/"


@pytest.mark.django_db
def test_seeker_can_save_a_published_job(auth, seeker_a, published_job):
    client = auth(seeker_a)
    r = client.post(SAVED, {"job": published_job.id}, format="json")
    assert r.status_code == 201
    assert SavedJob.objects.filter(user=seeker_a, job=published_job).exists()


@pytest.mark.django_db
def test_saving_same_job_twice_returns_409(auth, seeker_a, published_job):
    client = auth(seeker_a)
    client.post(SAVED, {"job": published_job.id}, format="json")
    r = client.post(SAVED, {"job": published_job.id}, format="json")
    assert r.status_code == 409
    assert SavedJob.objects.filter(user=seeker_a, job=published_job).count() == 1


@pytest.mark.django_db
def test_cannot_save_a_draft_job(auth, seeker_a, draft_job):
    """Saving a hidden job would leak that it exists -- same as Job.retrieve()."""
    client = auth(seeker_a)
    r = client.post(SAVED, {"job": draft_job.id}, format="json")
    assert r.status_code == 404
    assert not SavedJob.objects.filter(job=draft_job).exists()


@pytest.mark.django_db
def test_saving_nonexistent_job_returns_404(auth, seeker_a):
    client = auth(seeker_a)
    r = client.post(SAVED, {"job": 999999}, format="json")
    assert r.status_code == 404


@pytest.mark.django_db
def test_employer_cannot_save_jobs(auth, employer, published_job):
    client = auth(employer)
    r = client.post(SAVED, {"job": published_job.id}, format="json")
    assert r.status_code == 403


@pytest.mark.django_db
def test_anonymous_cannot_save_jobs(api_client, published_job):
    r = api_client.post(SAVED, {"job": published_job.id}, format="json")
    assert r.status_code == 401


@pytest.mark.django_db
def test_list_saved_jobs_returns_nested_job_data(auth, seeker_a, published_job):
    client = auth(seeker_a)
    client.post(SAVED, {"job": published_job.id}, format="json")
    r = client.get(SAVED)
    assert r.status_code == 200
    assert r.data[0]["job"]["title"] == published_job.title


@pytest.mark.django_db
def test_saved_jobs_are_scoped_to_the_requesting_user(auth, seeker_a, seeker_b, published_job):
    SavedJob.objects.create(user=seeker_b, job=published_job)
    client = auth(seeker_a)
    r = client.get(SAVED)
    assert r.data == []


@pytest.mark.django_db
def test_unsave_removes_the_bookmark(auth, seeker_a, published_job):
    client = auth(seeker_a)
    client.post(SAVED, {"job": published_job.id}, format="json")
    r = client.delete(f"{SAVED}{published_job.id}/")
    assert r.status_code == 204
    assert not SavedJob.objects.filter(user=seeker_a, job=published_job).exists()


@pytest.mark.django_db
def test_unsaving_a_job_not_saved_returns_404(auth, seeker_a, published_job):
    client = auth(seeker_a)
    r = client.delete(f"{SAVED}{published_job.id}/")
    assert r.status_code == 404


@pytest.mark.django_db
def test_cannot_unsave_another_users_saved_job(auth, seeker_a, seeker_b, published_job):
    SavedJob.objects.create(user=seeker_b, job=published_job)
    client = auth(seeker_a)
    r = client.delete(f"{SAVED}{published_job.id}/")
    assert r.status_code == 404
    assert SavedJob.objects.filter(user=seeker_b, job=published_job).exists()
