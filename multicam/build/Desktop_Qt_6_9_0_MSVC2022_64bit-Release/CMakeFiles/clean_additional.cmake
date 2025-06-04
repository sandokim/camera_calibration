# Additional clean files
cmake_minimum_required(VERSION 3.16)

if("${CONFIG}" STREQUAL "" OR "${CONFIG}" STREQUAL "Release")
  file(REMOVE_RECURSE
  "CMakeFiles\\multicam_autogen.dir\\AutogenUsed.txt"
  "CMakeFiles\\multicam_autogen.dir\\ParseCache.txt"
  "multicam_autogen"
  )
endif()
