
# import itertools
# import os
# from collections import namedtuple
# from typing import Iterable

# from icon_manager.config.user import UserConfig


# def find_paths(path):
#     my_paths = {}
#     for entry in os.scandir(path):
#         if not entry.is_dir():
#             continue
#         my_paths[entry.path] = find_paths(entry)
#     return my_paths


# def get_paths(configs: Iterable[UserConfig]):
#     paths = []
#     for config in configs:
#         for folder in config.search_folders:
#             paths.append(folder.path)
#     return paths


# def search_paths(configs: Iterable[UserConfig]):
#     paths = get_paths(configs)
#     dirs = {}
#     for entries in itertools.chain(os.scandir(path) for path in paths):
#         for entry in entries:
#             if not entry.is_dir():
#                 continue
#             dirs[entry.path] = find_paths(entry)
#         # p = Pool(len(paths))
#         # dirs = p.map(find_paths, paths)
#     return dirs


# def get_entries(entry: os.DirEntry) -> Dir:
#     files = []
#     folders = []
#     for folder in os.scandir(entry.path):
#         if folder.is_dir():
#             folders.append(get_entries(folder))
#         else:
#             files.append(File(path=folder.path, name=folder.name))
#     return Dir(path=entry.path, name=entry.name, files=files, folders=folders)


# def find_entries(path: str) -> Dir:
#     files = []
#     folders = []
#     for entry in os.scandir(path):
#         if entry.is_dir():
#             folders.append(get_entries(entry))
#         else:
#             files.append(File(path=entry.path, name=entry.name))
#     name = os.path.basename(path)
#     return Dir(path=path, name=name, files=files, folders=folders)
