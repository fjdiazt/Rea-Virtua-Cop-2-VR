#include <windows.h>
#include "vc2_share.h"

int main(void)
{
    HANDLE map = CreateFileMappingA(INVALID_HANDLE_VALUE, NULL, PAGE_READWRITE,
                                    0, sizeof(Vc2Frame), VC2_SHARE_NAME);
    Vc2Frame *frame;
    int i;
    if (!map) return 1;
    if (GetLastError() == ERROR_ALREADY_EXISTS) { CloseHandle(map); return 3; }
    frame = (Vc2Frame *)MapViewOfFile(map, FILE_MAP_ALL_ACCESS, 0, 0, sizeof(Vc2Frame));
    if (!frame) { CloseHandle(map); return 2; }
    frame->magic = VC2_SHARE_MAGIC;
    frame->version = VC2_SHARE_VERSION;
    frame->fov_degrees = 60.0f;
    frame->units_per_metre = 130.0f;
    for (i = 0; i < 1500 && GetFileAttributesA("exit.now") == INVALID_FILE_ATTRIBUTES; i++)
        Sleep(20);
    UnmapViewOfFile(frame);
    CloseHandle(map);
    return 0;
}
