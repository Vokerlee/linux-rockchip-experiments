CC = gcc
PARAMS = ARRAY_SIZE_LOG2=$(ARRAY_SIZE_LOG2) SHIFT_LOG2=$(SHIFT_LOG2)
FLAGS = -O0 -Wall -Wextra -Werror -static  \
	$(PARAMS:%=-D%)

BUILD_DIR = build
SRC_FILE = $(wildcard *.c)
OUT_FILE = $(BUILD_DIR)/$(basename $(SRC_FILE))_$(POSTFIX)

all:
	mkdir -p $(BUILD_DIR)
	$(CC) $(FLAGS) $(SRC_FILE) -o $(OUT_FILE)

clean:
	$(RM) -r $(BUILD_DIR)