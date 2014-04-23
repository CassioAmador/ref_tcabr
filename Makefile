TARGET   = ref_acq

CC		 = gcc
CFLAGS   = -std=c99 -Wall -I.
LINKER   = gcc -o
LFLAGS   = -Wall -I. -lm
SRCDIR   = ${CURDIR}/src
BINDIR   = ${CURDIR}/bin
FOLDERS  = ${CURDIR}/db  ${CURDIR}/data ${CURDIR}/logs

SOURCES  := $(wildcard $(SRCDIR)/*.c)
INCLUDES := $(wildcard $(SRCDIR)/*.h)
OBJECTS  := $(SOURCES:$(SRCDIR)/%.c=$(SRCDIR)/%.o)
rm		  = rm -f

$(BINDIR)/$(TARGET): $(OBJECTS)
		@$(LINKER) $@ $(LFLAGS) $(OBJECTS)

$(OBJECTS): $(SRCDIR)/%.o : $(SRCDIR)/%.c
		@$(CC) $(CFLAGS) -c $< -o $@

.PHONEY: config clean run

config:
		mkdir -p $(BINDIR) $(FOLDERS)

clean:
		@$(rm) $(OBJECTS)
		@$(rm) $(BINDIR)/$(TARGET)

run:
		python ref_setup.py