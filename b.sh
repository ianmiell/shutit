#!/bin/bash
#http://patorjk.com/software/taag
DATA[0]="      o/o/o/  o/                    o/      o/o/o/    o/      "
DATA[1]="   o/        o/o/o/    o/    o/  o/o/o/o/    o/    o/o/o/o/   "
DATA[2]="    o/o/    o/    o/  o/    o/    o/        o/      o/        "
DATA[3]="       o/  o/    o/  o/    o/    o/        o/      o/         "
DATA[4]="o/o/o/    o/    o/    o/o/o/      o/o/  o/o/o/      o/o/      "

DATA[0]=" ad88888ba   88                                 88           "
DATA[1]="d8^     ^8b  88                          ,d     88    ,d     "
DATA[2]="Y8,          88                          88     88    88     "
DATA[3]="'Y8aaaaa,    88,dPPYba,   88       88  MM88MMM  88  MM88MMM  "
DATA[4]="  '^^^^^8b,  88P'    &8a  88       88    88     88    88     "
DATA[5]="        '8b  88       88  88       88    88     88    88     "
DATA[6]="Y8a    'a8P  88       88  ^8a,   ,a88    88,    88    88,    "
DATA[7]=" ^Y88888P^   88       88   '^YbbdP'Y8    ^Y888  88    ^Y888  "
REALoOFFSEToX=0
REALoOFFSEToY=0
drawochar() {
  VoCOORDoX=$1
  VoCOORDoY=$2
  tput cup $((REALoOFFSEToY + VoCOORDoY)) $((REALoOFFSEToX + VoCOORDoX))
  printf %c ${DATA[VoCOORDoY]:VoCOORDoX:1}
}
trap 'exit 1' INT TERM
trap 'tput setaf 9; tput cvvis; clear' EXIT
tput civis
clear
for ((b=0; b<1; b++)); do
for ((c=1; c <= 5; c++)); do
  tput setaf $c
  for ((x=0; x<${#DATA[0]}; x++)); do
    for ((y=0; y<=7; y++)); do
      drawochar $x $y
    done
  done
done
done
