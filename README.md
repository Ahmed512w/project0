# Item Catalog App
Building an application that provides a list of items within a variety of categories as well as provide a user registration and authentication system. Registered users will have the ability to post, edit and delete their own items.

## System setup
This project makes use of Udacity's Linux-based virtual machine (VM) configuration which includes all of the necessary software to run the application.
1. Download [Vagrant](https://www.vagrantup.com/downloads.html) and install.
2. Download [Virtual Box](https://www.virtualbox.org/wiki/Download_Old_Builds_5_1) and install. 
3. Download the VM configuration file [FSND-Virtual-Machine.zip](https://s3.amazonaws.com/video.udacity-data.com/topher/2018/April/5acfbfa3_fsnd-virtual-machine/fsnd-virtual-machine.zip).


#### Run these commands from the terminal in the folder where your vagrant is installed in: 
1. ```vagrant up``` to start up the VM.
2. ```vagrant ssh``` to log into the VM.
3. ```cd /vagrant``` to change to your vagrant directory.
4. ```git clone https://github.com/Ahmed512w/Item_Catalog.git``` to Clone this repository 
5. ```python finalproject.py``` to run the application.


### DB:
    - database_setup.py has the classes for the databas_tables: User / Category / MenuItem

### Routes & function in project.py
    - routes and functions for login google:
        -- @app.route('/login/') - function showLogin() 
        -- @app.route('/gconnect', methods=['POST']) - function gconnect()
        -- @app.route('/disconnect') - function gdisconnect()
    - JSON APIs to view Category Information:
        -- @app.route('/category/<int:category_id>/menu/JSON') - function categoryMenuJSON(category_id)
        -- @app.route('/category/<int:category_id>/item/<int:menu_id>/JSON') - function menuItemJSON(category_id, menu_id)
        -- @app.route('/category/JSON') - function catalogJSON()
    - routes and functions for Item Catalog App:
        -- Show catalog: @app.route('/') / @app.route('/catalog/') - function showCatalog()
        -- Show a Category Items: @app.route('/category/<int:category_id>/items/') - function showMenu(category_id)
        -- Show an item description: @app.route('/category/<int:category_id>/item/<int:menuitem_id>/') - function showMenuItem(category_id, menuitem_id)
        -- Create a new menu item from the page of latest items: @app.route('/category/item/new/',methods=['GET','POST']) - function newMenuItem()
        -- Create a new menu item from the page of specified category: @app.route('/category/<int:category_id>/item/new/',methods=['GET','POST']) -             function newMenuItemWithCat(category_id)
        -- Edit a menu item: @app.route('/category/menu/<int:menuitem_id>/edit', methods=['GET','POST']) - function editMenuItem(menuitem_id)
        -- Delete a menu item: @app.route('/category/item/<int:menuitem_id>/delete', methods = ['GET','POST']) - function deleteMenuItem(menuitem_id)
        -- Disconnect based on provider: @app.route('/disconnect') - function disconnect()

### Static Folder:
    - styles.css has the required css for the html files

### Templates Folder: html files:
        - publiccatalog 
        - publicmenu
        - publicmenuitem
        - header
        - login 
        - majn
        - nav
        - catalog
        - menu 
        - menuitem 
        - newmenuitem 
        - deletemenuitem
        - editmenuitem

### Another files:
    - client_secrets.json: for the login processes with google
