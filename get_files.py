from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

gAuth = GoogleAuth('./config/settings.yaml')
gAuth.LocalWebserverAuth()

gDrive = GoogleDrive(gAuth)


def parse_gDrive_path(gd_path):

    if ':' in gd_path:
        gd_path = gd_path.split(':')[1]
    gd_path = gd_path.replace('\\', '/').replace('//', '/')
    if gd_path.startswith('/'):
        gd_path = gd_path[1:]
    if gd_path.endswith('/'):
        gd_path = gd_path[:-1]
    return gd_path.split('/')


def resolve_path_to_id(folder_path):

    _id = 'root'
    folder_path = parse_gDrive_path(folder_path)

    for idx, folder in enumerate(folder_path):
        folder_list = gDrive.ListFile(
            {'q': f"'{_id}' in parents and title='{folder}' and trashed=false and mimeType='application/vnd.google-apps.folder'", 'fields': 'items(id, title, mimeType)'}).GetList()
        _id = folder_list[0]['id']
        title = folder_list[0]['title']
        if idx == (len(folder_path) - 1) and folder == title:
            return _id

    return _id


def get_folder_files(folder_ids, batch_size=100):

    base_query = "'{target_id}' in parents"
    target_queries = []
    query = ''

    for idx, folder_id in enumerate(folder_ids):
        query += base_query.format(target_id=folder_id)
        if len(folder_ids) == 1 or idx > 0 and idx % batch_size == 0:
            target_queries.append(query)
            query = ''
        elif idx != len(folder_ids)-1:
            query += " or "
        else:
            target_queries.append(query)

    for query in target_queries:
        for f in gDrive.ListFile({'q': f"{query} and trashed=false", 'fields': 'items(id, title, mimeType, version, shared)'}).GetList():
            yield f


def get_files(folder_path=None, target_ids=None, files=[], is_recursive=True):

    base_share_url = "https://drive.google.com/file/d/{file_id}/view?usp=sharing"

    if target_ids is None and folder_path != '/':
        target_ids = [resolve_path_to_id(folder_path)]

    if folder_path == '/':
        target_ids = ['root']

    file_list = get_folder_files(folder_ids=target_ids, batch_size=250)

    subfolder_ids = []

    for f in file_list:
        if f['mimeType'] == 'application/vnd.google-apps.folder':
            subfolder_ids.append(f['id'])
        else:
            f['shareURL'] = base_share_url.format(
                file_id=f['id']) if f['shared'] == True else None
            files.append(f)

    if len(subfolder_ids) > 0 and is_recursive == True:
        get_files(target_ids=subfolder_ids)

    return files
