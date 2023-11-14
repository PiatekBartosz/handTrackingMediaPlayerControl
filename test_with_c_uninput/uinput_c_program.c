#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <linux/uinput.h>

int main() {
    int fd = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
    if (fd < 0) {
        perror("Failed to open /dev/uinput");
        return EXIT_FAILURE;
    }

    struct uinput_setup usetup;
    memset(&usetup, 0, sizeof(usetup));
    usetup.id.bustype = BUS_USB;
    usetup.id.vendor = 0x1;
    usetup.id.product = 0x1;
    strncpy(usetup.name, "uinput-c-program", UINPUT_MAX_NAME_SIZE);

    if (ioctl(fd, UI_DEV_SETUP, &usetup) < 0) {
        perror("Failed to setup uinput device");
        close(fd);
        return EXIT_FAILURE;
    }

    if (ioctl(fd, UI_DEV_CREATE) < 0) {
        perror("Failed to create uinput device");
        close(fd);
        return EXIT_FAILURE;
    }

    // Simulate a key press (replace this with your uinput logic)
    struct input_event ev;
    memset(&ev, 0, sizeof(struct input_event));
    ev.type = EV_KEY;
    ev.code = KEY_A;
    ev.value = 1;

    if (write(fd, &ev, sizeof(struct input_event)) < 0) {
        perror("Failed to write key press event");
        close(fd);
        return EXIT_FAILURE;
    }

    // Simulate a key release (replace this with your uinput logic)
    ev.value = 0;

    if (write(fd, &ev, sizeof(struct input_event)) < 0) {
        perror("Failed to write key release event");
        close(fd);
        return EXIT_FAILURE;
    }

    // Clean up
    if (ioctl(fd, UI_DEV_DESTROY) < 0) {
        perror("Failed to destroy uinput device");
    }

    close(fd);

    return EXIT_SUCCESS;
}
