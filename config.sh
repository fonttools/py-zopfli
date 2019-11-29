# Define custom utilities
# Test for OSX with [ -n "$IS_OSX" ]

function pre_build {
    # Any stuff that you need to do before you start building the wheels
    # Runs in the root directory of this repository.
    :
}

function run_tests {
    # The function is called from an empty temporary directory, so we do
    # '..' to get the path to the compiled wheel
    wheelhouse=$(abspath ../wheelhouse)
    wheel=`ls ${wheelhouse}/zopfli*.whl | head -n 1`

    # automatically select tox environment based on current python version
    if [ -n "$IS_OSX" ]; then
        # $PYTHON_VERSION is only exported in the Linux docker container
        PYTHON_VERSION=$MB_PYTHON_VERSION
    fi
    case "${PYTHON_VERSION}" in
        2.7)
           TOXENV=py27
           ;;
        3.5)
           TOXENV=py35
           ;;
        3.6)
           TOXENV=py36
           ;;
        3.7)
           TOXENV=py37
           ;;
        3.8)
           TOXENV=py38
           ;;
    esac

    # Installed wheel inside the tox environment and runs the tests on it
    tox --installpkg $wheel -e $TOXENV
}
