import openpyxl
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib.request as req

main_url = "https://web.archive.org/"
session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount("http://", adapter)
session.mount("https://", adapter)
DATA = "data/"


def _url_replaces(url: str):
    # data = {
    #     ":": "%3A",
    #     "=": "%3D",
    #     "?": "%3F",
    #     # "/": "\\%\\2\\F",
    #     "&": "%26",
    #     " ": "%20",
    # }
    # for key, value in data.items():
    #     url = url.replace(key, value)
    # return url
    return req.pathname2url(url)


def _url_builder(extra_url, **kwargs):
    extra_url = _url_replaces(extra_url)
    url_without_args = f"{main_url}{extra_url}"
    args = []
    for arg, value in kwargs.items():
        args.append(f"{arg}={value}")
    return url_without_args + ("?" + "&".join(args) if args else "")


def create_dir(file):
    os.makedirs(DATA + "/".join(file.split("/")[:-1]))
    print(f"Directory {file} was created")


def is_dir_exists(file):
    return os.path.exists(DATA + "/".join(file.split("/")[:-1]))


def create_file(file, img):
    with open(DATA + file, "wb") as f:
        f.write(img)
        print(f"Downloaded file {file}")


def create_file_path(file):
    if file.count("/") < 1:
        print("This is a file")
    else:
        print("This is a dir with file")
        if not is_dir_exists(file):
            create_dir(file)


def is_url_valid(responce):
    if responce.status_code != 200:
        return False
    return True


def is_file_exists(file):
    if os.path.exists(DATA + file):
        return True
    return False


def get_excel_cells():
    file = "data.xlsx"
    wb = openpyxl.load_workbook(file, read_only=True)
    ws = wb.active
    cells = []
    for row in ws.rows:
        for cell in row:
            if cell.value is not None:
                cells.append(cell.value)

    return set(cells)


def get_snaps_timesplamps(url):
    url = _url_replaces(url)
    api_scaps = session.get(
        _url_builder(
            "__wb/calendarcaptures/2",
            url=url,
            date="202",
        )
    ).json()["items"]
    snaps_days = []
    for item in api_scaps:
        snaps_days.append(str(item[0]))

    return snaps_days


def get_all_urls():
    api_urls = session.get(
        _url_builder(
            "web/timemap/json",
            url="tayga.city",
            matchType="prefix",
            collapse="urlkey",
            output="json",
            fl=(
                "original%2Cmimetype%2Ctimestamp%2Cendtimestamp%2"
                "Cgroupcount%2Cuniqcount"
            ),
            filter="!statuscode%3A[45]..",
            limit="10000",
            _="1678811637944",
        )
    ).json()[1:]
    urls = []
    for url in api_urls:
        if url[1] == "text/html":
            urls.append(url[0])
    return urls


def is_files_to_download(files):
    return files


def main():
    files = get_excel_cells()

    urls = get_all_urls()

    for i, url in enumerate(urls, start=1):
        print(f"Url {url} {i} of {len(urls)}")
        url_snap = get_snaps_timesplamps(url)[-1]
        print(f"Curent snap: 202{url_snap}")
        files_to_remove = []
        if not is_files_to_download(files):
            print("Download complite!")
            return
        for i, row_file in enumerate(files, start=1):
            print(f"File {i} of {len(files)} ({row_file})")
            file = row_file[1:]
            url = _url_builder(
                (
                    "web/"
                    f"202{url_snap}im_/"
                    "https://storage.yandexcloud.net/"
                    "tayga-city-static/"
                    f"{file}"
                ),
            )
            if is_file_exists(file):
                print(f"File {file} already exists!")
                files_to_remove.append("/" + file)
                continue
            responce = session.get(url)
            if not is_url_valid(responce):
                continue
            print(f"Found file {file}")
            img = responce.content
            create_file_path(file)
            create_file(file, img)
            files_to_remove.append("/" + file)
        print(f"Downloaded {len(files_to_remove)} files from snap {url_snap}")
        print("Update files")
        for file_to_remove in files_to_remove:
            files.remove(file_to_remove)
            print(f"File {file_to_remove} was deleted from files")
        print(f"Files to download: {len(files)}")


if __name__ == "__main__":
    main()
