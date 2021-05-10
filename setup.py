from setuptools import setup, find_packages

from photons_messages_generator import VERSION

# fmt: off

setup(
      name = "lifx-photons-messages-generator"
    , version = VERSION
    , packages = ["photons_messages_generator"] + ["photons_messages_generator.{0}".format(pkg) for pkg in find_packages("photons_messages_generator")]
    , include_package_data = True

    , install_requires =
      [ "delfick_project==0.7.9"
      , "rainbow_logging_handler==2.2.2"
      , "ruamel.yaml==0.17.4"
      ]

    , extras_require =
      { "tests":
        [ "noseOfYeti==2.0.2"
        , "pytest==6.1.2"
        ]
      }

    , entry_points =
      { 'console_scripts' :
        [ 'generate_photons_messages = photons_messages_generator.executor:main'
        ]
      }

    # metadata for upload to PyPI
    , url = "http://github.com/delfick/photons-messages-generator"
    , author = "Stephen Moore"
    , author_email = "delfick755@gmail.com"
    , description = "Code for generating the photons_messages module"
    , long_description = open("README.rst").read()
    , license = "MIT"
    , keywords = "lifx photons"
    )

# fmt: on
