TARGET   = ref_acq

CC		   = gcc
CFLAGS   = -std=c99 -Wall -I.
LINKER   = gcc -o
LFLAGS   = -Wall -I. -lm
BINDIR   = ${CURDIR}/../bin

SOURCES  := $(wildcard *.c)
INCLUDES := $(wildcard *.h)
OBJECTS  := $(SOURCES:%.c=%.o)
rm		  = rm -f


$(BINDIR)/$(TARGET): $(OBJECTS)
		@$(LINKER) $@ $(LFLAGS) $(OBJECTS)

$(OBJECTS): %.o : %.c
		@$(CC) $(CFLAGS) -c $< -o $@

.PHONEY: clean
clean:
		@$(rm) $(OBJECTS)
		@$(rm) $(BINDIR)/$(TARGET)
