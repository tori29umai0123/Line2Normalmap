import sys
from modules import cmd_args


args, _ = cmd_args.parser.parse_known_args()



def start():
    print(f"Launching {'API server' if '--nowebui' in sys.argv else 'Web UI'} with arguments: {' '.join(sys.argv[1:])}")
    import Line2Normalmap_gui
    Line2Normalmap_gui.api_only()

    from modules_forge import main_thread

    main_thread.loop()
    return


def dump_sysinfo():
    from modules import sysinfo
    import datetime

    text = sysinfo.get()
    filename = f"sysinfo-{datetime.datetime.utcnow().strftime('%Y-%m-%d-%H-%M')}.json"

    with open(filename, "w", encoding="utf8") as file:
        file.write(text)

    return filename
