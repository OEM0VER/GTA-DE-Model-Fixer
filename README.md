![alt text](https://i.imgur.com/IzeMm1h.png)

# Uasset-Model-Fixer
A lightweight tool for repairing broken Unreal Engine models `.uasset`/`.uexp` for GTA Trilogy DE and packing/unpacking `.pak` files with drag-and-drop simplicity.

# **Key features include:**

- **Model Repair:**  
  - Fixes `.uasset` files with serialization errors using [Hypermodule’s MeshAibRemover](https://github.com/hypermodule/MeshAibRemover), powered by [CUE4Parse](https://github.com/FabianFG/CUE4Parse).  
  - **New:** Supports fixing multiple models at once for faster workflows.

- **PAK Management:**  
  - Drag a **folder** → creates an uncompressed `.pak` file in the same folder.  
  - Drag a **.pak file** → unpacks its contents to the **Desktop**.  
  - Files are automatically organized based on what you dragged.

- **Automatic Setup:** Downloads required resources on first launch, ensuring everything works out of the box.  

- **User-Friendly Interface:** Dark-themed window with hover effects, custom fonts, and clickable links to related resources.  

- **Persistent Window Position:** Remembers the last screen and position the app was opened in for consistent workflow.  

- **Integrated Shortcuts:** Quickly create a desktop shortcut for faster access.

- **Integrated Tools & Tutorials:** Access helpful links and tutorials directly from the **Tools** and **Help** menus in the top bar.  

Designed to assist both modders and developers, **Model Fixer** saves time and effort when working with Unreal Engine models and archives, making asset repair and packaging a seamless process.

## Credits  

This project would not be possible without the amazing work of others:  

- **[Hypermodule’s AIBRemover](https://github.com/hypermodule/AIBRemover)** – Provides the core functionality for repairing Unreal Engine `.uasset` files.  
- **[CUE4Parse](https://github.com/FabianFG/CUE4Parse)** – The powerful Unreal Engine asset parser that AIBRemover is built upon.
- **[UnrealPak](https://github.com/xamarth/unrealpak)** – Used for packing and unpacking .pak files.  

Special thanks to their developers for making these tools available to the community 👏
