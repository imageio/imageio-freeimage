from setuptools.command.develop import develop
from setuptools.command.build_clib import build_clib

from distutils.errors import DistutilsSetupError
from distutils import log
from setuptools.dep_util import newer_pairwise_group
import platform
from pathlib import Path
import shutil
import requests
import zipfile
import io


class CustomDevelop(develop):
    def run(self) -> None:
        # download freeimage
        if not Path("FreeImage").exists():
            r = requests.get(
                "https://sourceforge.net/projects/freeimage/files/Source%20Distribution/3.18.0/FreeImage3180.zip/download"
            )
            z = zipfile.ZipFile(io.BytesIO(r.content))
            z.extractall(".")

        # build freeimage
        self.run_command("build_clib")

        super().run()


class CustomBuildClib(build_clib):
    user_options = build_clib.user_options + [
        (
            "shared-location=",
            "s",
            "copy the shared C/C++ libraries here after linking.",
        ),
    ]

    def initialize_options(self) -> None:
        self.shared_location = None
        super().initialize_options()

    def run(self) -> None:
        super().run()

        if self.shared_location is not None and self.libraries is not None:
            out_dir = Path(self.shared_location)
            out_dir.mkdir(exist_ok=True, parents=True)
            build_dir = Path(self.build_clib)
            for (lib_name, build_info) in self.libraries:
                if not build_info.get("shared", False):
                    continue

                file_name = self.compiler.library_filename(lib_name, lib_type="shared")

                shutil.copy(str(build_dir / file_name), str(out_dir / file_name))

    def build_libraries(self, libraries):
        # Note: this is a copy of build_clib except for the part marked below

        for (lib_name, build_info) in libraries:
            sources = build_info.get("sources")
            if sources is None or not isinstance(sources, (list, tuple)):
                raise DistutilsSetupError(
                    "in 'libraries' option (library '%s'), "
                    "'sources' must be present and must be "
                    "a list of source filenames" % lib_name
                )
            sources = list(sources)

            log.info("building '%s' library", lib_name)

            # Make sure everything is the correct type.
            # obj_deps should be a dictionary of keys as sources
            # and a list/tuple of files that are its dependencies.
            obj_deps = build_info.get("obj_deps", dict())
            if not isinstance(obj_deps, dict):
                raise DistutilsSetupError(
                    "in 'libraries' option (library '%s'), "
                    "'obj_deps' must be a dictionary of "
                    "type 'source: list'" % lib_name
                )
            dependencies = []

            # Get the global dependencies that are specified by the '' key.
            # These will go into every source's dependency list.
            global_deps = obj_deps.get("", list())
            if not isinstance(global_deps, (list, tuple)):
                raise DistutilsSetupError(
                    "in 'libraries' option (library '%s'), "
                    "'obj_deps' must be a dictionary of "
                    "type 'source: list'" % lib_name
                )

            # Build the list to be used by newer_pairwise_group
            # each source will be auto-added to its dependencies.
            for source in sources:
                src_deps = [source]
                src_deps.extend(global_deps)
                extra_deps = obj_deps.get(source, list())
                if not isinstance(extra_deps, (list, tuple)):
                    raise DistutilsSetupError(
                        "in 'libraries' option (library '%s'), "
                        "'obj_deps' must be a dictionary of "
                        "type 'source: list'" % lib_name
                    )
                src_deps.extend(extra_deps)
                dependencies.append(src_deps)

            expected_objects = self.compiler.object_filenames(
                sources,
                output_dir=self.build_temp,
            )

            if newer_pairwise_group(dependencies, expected_objects) != ([], []):
                # First, compile the source code to object files in the library
                # directory.  (This should probably change to putting object
                # files in a temporary build directory.)
                self.compiler.compile(
                    sources,
                    output_dir=self.build_temp,
                    macros=build_info.get("macros"),
                    include_dirs=build_info.get("include_dirs"),
                    extra_preargs=build_info.get("compiler_preargs"),
                    extra_postargs=build_info.get("compiler_postargs"),
                    debug=self.debug,
                )

            if build_info.get("shared", False):
                # This part is __NEW__. It checks for a flag called
                # "shared" and then compiles a shared library instead of an archive.

                if platform.system() == "Windows":
                    # On windows (MSVC) we need to tell the compiler to make a DLL
                    preargs = ["/DLL"] + build_info.get("linker_preargs", list())
                else:
                    preargs = ["-shared"] + build_info.get("linker_preargs", list())

                self.compiler.link_shared_lib(
                    expected_objects,
                    lib_name,
                    output_dir=self.build_clib,
                    debug=self.debug,
                    extra_preargs=preargs,
                    extra_postargs=build_info.get("linker_postargs", None),
                    libraries=build_info.get("libraries"),
                    library_dirs=build_info.get("library_dirs", list())
                    + [self.build_clib],
                )
            else:
                # Now "link" the object files together into a static library.
                # (On Unix at least, this isn't really linking -- it just
                # builds an archive.  Whatever.)
                self.compiler.create_static_lib(
                    expected_objects,
                    lib_name,
                    output_dir=self.build_clib,
                    debug=self.debug,
                )


def build(setup_kwargs):
    if platform.system() == "Windows":
        import win32_conf as conf

        libraries = [
            (
                "zlib",
                {
                    "sources": conf.ZLib.source,
                    "include_dirs": conf.ZLib.include,
                    "macros": conf.ZLib.macros,
                },
            ),
            (
                "jxr",
                {
                    "sources": conf.LibJXR.source,
                    "include_dirs": conf.LibJXR.include,
                    "macros": conf.LibJXR.macros,
                },
            ),
            (
                "openexr",
                {
                    "sources": conf.OpenEXR.source,
                    "include_dirs": conf.OpenEXR.include,
                    "macros": conf.OpenEXR.macros,
                },
            ),
            (
                "webp",
                {
                    "sources": conf.LibWebP.source,
                    "include_dirs": conf.LibWebP.include,
                    "macros": conf.LibWebP.macros,
                },
            ),
            (
                "tiff4",
                {
                    "sources": conf.LibTIFF4.source,
                    "include_dirs": conf.LibTIFF4.include,
                    "macros": conf.LibTIFF4.macros,
                },
            ),
            (
                "rawlite",
                {
                    "sources": conf.LibRawLite.source,
                    "include_dirs": conf.LibRawLite.include,
                    "macros": conf.LibRawLite.macros,
                },
            ),
            (
                "png",
                {
                    "sources": conf.LibPNG.source,
                    "include_dirs": conf.LibPNG.include,
                    "macros": conf.LibPNG.macros,
                },
            ),
            (
                "openjpeg",
                {
                    "sources": conf.LibOpenJPEG.source,
                    "include_dirs": conf.LibOpenJPEG.include,
                    "macros": conf.LibOpenJPEG.macros,
                },
            ),
            (
                "jpeg",
                {
                    "sources": conf.LibJPEG.source,
                    "include_dirs": conf.LibJPEG.include,
                    "macros": conf.LibJPEG.macros,
                },
            ),
            (
                "freeimage",
                {
                    "shared": True,
                    "sources": conf.FreeImage.source,
                    "include_dirs": conf.FreeImage.include,
                    "macros": conf.FreeImage.macros,
                    "libraries": conf.FreeImage.libraries,
                },
            ),
        ]
    else:
        import linux_conf as conf

        libraries = [
            (
                "freeimage",
                {
                    "shared": True,
                    "sources": conf.FreeImage.source,
                    "include_dirs": conf.FreeImage.include,
                    "macros": conf.FreeImage.macros,
                    "libraries": conf.FreeImage.libraries,
                    "compiler_preargs": conf.FreeImage.preflags,
                    "compiler_postargs": conf.FreeImage.cflags,
                    "linker_preargs": conf.FreeImage.linker_preargs,
                    "linker_postargs": conf.FreeImage.linker_postargs,
                },
            ),
        ]

    setup_kwargs.update(
        {
            "libraries": libraries,
            "options": {
                "build_clib": {
                    "shared_location": "imageio_freeimage/_lib",
                    "debug": False,
                }
            },
            "cmdclass": {"develop": CustomDevelop, "build_clib": CustomBuildClib},
        }
    )
