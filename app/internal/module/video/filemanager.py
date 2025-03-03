import glob
import shutil
import os

import datetime
import json
import aiofiles
import asyncio
from functools import wraps, partial
import string
import random
from fastapi import File, UploadFile


class filemanager_class:
    def __init__(self):
        self.m3u8 = {
            "init": [
                "#EXTM3U",
                "#EXT-X-VERSION:3",
            ],
            "audio": [
                (
                    "#EXT-X-MEDIA:TYPE=AUDIO,"
                    "GROUP-ID=\"audio\",NAME=\"Audio\",LANGUAGE=\"ja\","
                    "AUTOSELECT=YES,URI=\"audio.m3u8\""
                )],
            240: [
                (
                    "#EXT-X-STREAM-INF:BANDWIDTH=250000,"
                    "RESOLUTION=426x240,AUDIO=\"audio\""
                ),
                "240p.m3u8"],
            360: [
                (
                    "#EXT-X-STREAM-INF:BANDWIDTH=650000,"
                    "RESOLUTION=640x360,AUDIO=\"audio\""
                ),
                "360p.m3u8"],
            480: [
                (
                    "#EXT-X-STREAM-INF:BANDWIDTH=1200000,"
                    "RESOLUTION=854x480,AUDIO=\"audio\""
                ),
                "480p.m3u8"],
            720: [
                (
                    "#EXT-X-STREAM-INF:BANDWIDTH=2300000,"
                    "RESOLUTION=1280x720,AUDIO=\"audio\""
                ),
                "720p.m3u8"],
            1080: [
                (
                    "#EXT-X-STREAM-INF:BANDWIDTH=4300000,"
                    "RESOLUTION=1920x1080,AUDIO=\"audio\""
                ),
                "1080p.m3u8"],
        }
        # 保存先のビデオフォルダ
        self.video_dir = "video"

    def async_wrap(self, func):
        @wraps(func)
        async def run(*args, loop=None, executor=None, **kwargs):
            if loop is None:
                loop = asyncio.get_event_loop()
            pfunc = partial(func, *args, **kwargs)
            return await loop.run_in_executor(executor, pfunc)
        return run

    def GetRandomStr(self, num) -> str:
        # 英数字をすべて取得
        dat = string.digits + string.ascii_lowercase + string.ascii_uppercase
        # 英数字からランダムに取得
        return ''.join([random.choice(dat) for i in range(num)])

    def remove_duplicates(self, _dict: dict) -> dict:
        """
        辞書内のリストの重複を排除する関数
        """
        for key in _dict:
            if isinstance(_dict[key], list):
                _dict[key] = list(set(_dict[key]))
        return _dict

    async def read_json(self, json_file):
        """
        info.jsonを読み込む関数
        """
        try:
            async with aiofiles.open(json_file, "r") as f:
                json_str = await f.read()
                _dict = json.loads(json_str)
        except FileNotFoundError:
            return False
        else:
            return _dict

    def write_json(self, json_file, _dict):
        """
        info.jsonに書き込む関数
        """
        # 重複の削除
        _dict = self.remove_duplicates(_dict)
        # 更新日の更新
        utc = datetime.timezone.utc
        _dict["updated_at"] = datetime.datetime.now(utc).isoformat()
        # エンコードタスクが完了している場合は削除
        for i in _dict["encode_tasks"]:
            if i in _dict["resolution"]:
                _dict["encode_tasks"].remove(i)
        # ファイル書き込み
        try:
            with open(json_file, "w") as f:
                json.dump(_dict, f, indent=4)
        except BaseException:
            return False
        else:
            return True

    async def write_file(self, file_path, in_file: UploadFile = File(...)):
        in_file.file.seek(0)
        async with aiofiles.open(file_path, 'wb') as out_file:
            while True:
                # 書き込みサイズ(MB)
                chunk = 32
                # async read chunk
                content = await in_file.read(chunk * 1048576)
                if content:
                    await out_file.write(content)  # async write chunk
                else:
                    break

    async def write_playlist(
            self, playlist_file: str, resolution: str = "init"):
        """
        m3u8のプレイリストを作成する関数
        """
        write_data = []
        if resolution == "init":
            write_data.extend(self.m3u8["init"])
            write_mode = "w"
        elif resolution == "audio":
            write_data.extend(self.m3u8["audio"])
            write_mode = "a"

        # 解像度の情報追加
        else:
            write_mode = "a"
            # 1080 or 1080p に対する対策
            try:
                resolution = int(resolution)
            except ValueError:
                resolution = int(resolution[:-1])
            if resolution in self.m3u8:
                write_data.extend(self.m3u8[resolution])
        # 書き込み
        async with aiofiles.open(playlist_file, mode=write_mode) as f:
            # print('\n'.join(write_data))
            await f.write("\n".join(write_data) + "\n")

    async def create_directory(self, year, cid, title, explanation) -> str:
        """
        ビデオディレクトリの作成関数
        """
        _created_dir = None
        while True:
            try:
                _created_dir = "/".join([self.video_dir, str(year),
                                        cid, self.GetRandomStr(10)])
                await self.async_wrap(os.makedirs)(_created_dir)
            except FileExistsError:
                pass
            else:
                break
        utc = datetime.timezone.utc
        dict_template = {
            "title": title,
            "explanation": explanation,
            "created_at": datetime.datetime.now(utc).isoformat(),
            "resolution": [],
            "encode_tasks": [],
            "encode_error": [],
        }
        self.write_json(_created_dir + "/info.json", dict_template)
        await self.write_playlist(_created_dir + "/playlist.m3u8", "init")
        return _created_dir

    async def delete_directory(self, year, cid, vid):
        """
        ビデオディレクトリの削除関数
        """
        _delete_dir = "/".join([self.video_dir, str(year), cid, vid])
        try:
            await self.async_wrap(shutil.rmtree)(_delete_dir)
        except Exception:
            return False
        else:
            return True

    async def delete_video(self, year, cid, vid):
        _delete_dir = "/".join([self.video_dir, str(year), cid, vid])
        # info.json以外削除
        for filepath in glob.glob(f"{_delete_dir}/*"):
            if "info.json" in filepath:
                pass
            else:
                os.remove(filepath)
        # プレイリストの初期化
        playlist_file = "/".join([self.video_dir, str(year),
                                 cid, vid, "playlist.m3u8"])
        await self.write_playlist(playlist_file, "init")
        # 既存のjsonを読み込み
        json_file = "/".join([self.video_dir, str(year),
                             cid, vid, "info.json"])
        _dict = await self.read_json(json_file)
        if not _dict:
            return False
        # jsonの更新
        _dict["resolution"] = []
        _dict["encode_tasks"] = []
        _dict["encode_error"] = []

        # jsonの書き込み
        if self.write_json(json_file, _dict):
            return True
        return False


filemanager = filemanager_class()
