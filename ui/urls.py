from django.urls import path

from ui import views

urlpatterns = [
    path("", views.workspace, name="workspace"),
    path("objects/", views.object_list, name="object-list"),
    path("objects/browse/", views.object_browse, name="object-browse"),
    path("objects/import/", views.import_object, name="import-object"),
    path("objects/<uuid:object_id>/update/", views.update_object_view, name="update-object"),
    path("objects/<uuid:object_id>/link/", views.link_object_view, name="link-object"),
    path("objects/<uuid:object_id>/type/", views.type_object_view, name="type-object"),
    path("objects/<uuid:object_id>/", views.object_detail, name="object-detail"),
    path("objects/<uuid:object_id>/edit/", views.apply_view_edit_view, name="apply-view-edit"),
    path("log/", views.event_log, name="event-log"),
    path("proposals/", views.submit_prompt, name="submit-prompt"),
    path("blobs/<str:sha256>/", views.blob_content, name="blob-content"),
]
