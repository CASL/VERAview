IF ( NOT DEFINED PYTHON_EXECUTABLE )
  FIND_PROGRAM( PYTHON_EXECUTABLE NAMES python )
ENDIF()

ADD_CUSTOM_TARGET(
    compile_python ALL
    ${PYTHON_EXECUTABLE} -m compileall
        "bean/*.py" "data/*.py" "event/*.py"
	"widget/*.py" "widget/bean/*.py"
	"view3d/*.py"
	"*.py"
    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
    COMMENT "Compiling VERAView python sources"
    )
