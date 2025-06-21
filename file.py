from mimetypes import guess_type

from requests import post


def upload_file(file_path: str, comment: str) -> str:
    mime_type, _ = guess_type(file_path)

    if mime_type is None:
        raise Exception("Unknown MIME type")

    response = post(
        'https://tnd.quest/upload.php',
        files=dict(
            file=(file_path.split('/')[-1], open(file_path, 'rb'), mime_type)
        ),
        data=dict(
            comment=comment,
            visibility=1
        ),
        headers=dict(
            accept='application/json'
        )
    )

    if response.status_code == 201:
        j = response.json()
        return j['data']['urls']['download_url']
    else:
        raise Exception(f"Failed to send a file ({response.status_code}): {response.text}")
