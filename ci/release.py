#!/usr/bin/env python3
##################
# Original from https://github.com/abusesa/github-release/blob/master/scripts/github-release
##################
import argparse
import mimetypes
import os
import re

import requests


def main():
    parser = argparse.ArgumentParser(description="Backup GitHub repositories.")
    parser.add_argument('--repository', help='name of the repository')
    parser.add_argument('--version', help='version to be released')
    parser.add_argument('--commit', help='commit of this version')
    parser.add_argument('--exclusive', action='store_true', help='fail if the release already exists')
    parser.add_argument('--prerelease', action='store_true', help='mark the release as prerelease')
    parser.add_argument('--token', help='github token')
    parser.add_argument('--asset', help='upload asset')
    parser.add_argument('--tagging', action='store_true', help='tag version')
    parser.add_argument('--latest', action='store_true', help='tag as latest')

    args = parser.parse_args()

    check_name(args.version)
    repo = args.repository
    version = args.version
    commit = args.commit
    exclusive = args.exclusive
    prerelease = args.prerelease
    token = args.token
    asset = args.asset
    latest = args.latest
    tagging = args.tagging

    if asset:
        with open(asset, 'rb') as file_obj:
            if os.fstat(file_obj.fileno()).st_size == 0:
                raise RuntimeError(f'can not attach empty file {asset}')

    print(f'Check for release')
    created, release = create_release(token=token, repo=repo,
                                      tag=version, commit_hash=commit,
                                      exclusive=exclusive, prerelease=prerelease)
    if created:
        print(f'Created a new release {release["name"]}')
    else:
        print(f'Already existing release {release["name"]}')

    if tagging:
        print(f'Tagging commit {commit} with {version}')
        create_tag(token=token, repo=repo,
                   tag=version, commit_hash=commit)

        if latest:
            print(f'Tag as latest')
            delete_tag(token=token, repo=repo,
                       tag='latest')
            create_tag(token=token, repo=repo,
                       tag='latest', commit_hash=commit)

    # upload_url is given in uri-template form. We could
    # use a package for this...
    upload_url, _, _ = release["upload_url"].partition("{")

    if asset:
        if upload_asset(token=token, upload_url=upload_url, filename=asset):
            print(f'Uploaded asset {asset}')
        else:
            print(f'Skipped already existing asset {asset}')


def check_name(name):
    if not re.match(r"^\w[-\.\w]*$", name):
        raise RuntimeError(f"invalid name '{name}'")


def create_tag(token, repo, tag, commit_hash):
    response = requests.post(
        f'https://api.github.com/repos/{repo}/git/tags',
        json={
            'tag': tag,
            'message': tag,
            'object': commit_hash,
            'type': 'commit'
        },
        headers={'Authorization': f'token {token}'}
    )
    print(response)
    print(response.json())


def delete_tag(token, repo, tag):
    response = requests.delete(
        f'https://api.github.com/repos/{repo}/git/refs/{tag}',
        headers={'Authorization': f'token {token}'}
    )
    print(response)
    print(response.json())


def already_exists(response, field):
    if response.status_code != 422:
        return False

    for error in response.json().get("errors", []):
        if error.get("field") != field or error.get("code") != "already_exists":
            return False

    return True


def create_release(token, repo, tag, commit_hash, exclusive=False, prerelease=False):
    response = requests.post(
        f'https://api.github.com/repos/{repo}/releases',
        json={
            'tag_name': tag,
            'name': tag,
            'prerelease': prerelease,
            'target_commitish': commit_hash
        },
        headers={'Authorization': f'token {token}'}
    )
    print(response)
    print(response.json())

    if already_exists(response, 'tag_name') and not exclusive:
        response = requests.get(
            f'https://api.github.com/repos/{repo}/releases/tags/{tag}',
            headers={'Authorization': f'token {token}'}
        )

        response.raise_for_status()
        return False, response.json()

    response.raise_for_status()
    return True, response.json()


def upload_asset(token, upload_url, filename):
    content_type, _ = mimetypes.guess_type(filename)

    if content_type is None:
        content_type = 'application/octet-stream'

    with open(filename, 'rb') as file_obj:
        response = requests.post(
            upload_url,
            data=file_obj,
            params={
                'name': os.path.basename(filename)
            },
            headers={
                'Authorization': f'token {token}',
                'Content-Type': content_type
            }
        )

    if already_exists(response, "name"):
        return False

    response.raise_for_status()
    return True


if __name__ == '__main__':
    main()
