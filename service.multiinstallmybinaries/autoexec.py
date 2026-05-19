from plugin import Installer
import json

m = Installer()

def main():
    m.create_folder(m.addon_data)
        
    if m.get_setting("activate_installer") == 'true':
        m.installer()
    else:
        quit()

if __name__ == "__main__":
    main()
