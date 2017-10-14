SET dir=D:\db-filler\generated_scripts\OUTPUT_results\
SET dst=D:\db-filler\generated_scripts\OUTPUT_results\to_process\
move /-y %dir%A\*.txt %dst%
move /-y %dst%*.txt %dir%A
move /-y %dir%B\*.txt %dst%
move /-y %dst%*.txt %dir%B
move /-y %dir%C\*.txt %dst%
move /-y %dst%*.txt %dir%C
move /-y %dir%D\*.txt %dst%
move /-y %dst%*.txt %dir%D
move /-y %dir%E\*.txt %dst%
move /-y %dst%*.txt %dir%E
move /-y %dir%F\*.txt %dst%
move /-y %dst%*.txt %dir%F
move /-y %dir%G\*.txt %dst%
move /-y %dst%*.txt %dir%G
move /-y %dir%H\*.txt %dst%
move /-y %dst%*.txt %dir%H
move /-y %dir%I\*.txt %dst%
move /-y %dst%*.txt %dir%I
move /-y %dir%J\*.txt %dst%
move /-y %dst%*.txt %dir%J
pause
