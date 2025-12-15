# PyMOL Visualization - User Guide

## Quick Start

### 1. Launch PyMOL Viewer

1. Navigate to your completed job's details page
2. Click the **"🔬 Visualize in PyMOL"** button
3. Wait for the viewer to load (this may take 10-30 seconds)

### 2. Load Your Results

Once PyMOL loads, you'll see the command on the page. Type it in the PyMOL console using Tab autocomplete:

**Step-by-step:**

1. Click inside the PyMOL console (bottom of the viewer window)
2. Type: `@/data/`
3. Press `Tab` to see available sessions
4. Select your session folder (it will start with your user ID)
5. Type: `/load_results.pml`
6. Press `Enter`

Your structures will load automatically! 🎉

**Pro Tip:** Tab autocomplete makes this fast and error-free. Just type `@/data/` + `Tab` and select your session.

## Navigating in PyMOL

### Mouse Controls

- **Rotate:** Left-click and drag
- **Zoom:** Scroll wheel OR right-click and drag up/down
- **Pan:** Middle-click and drag OR Shift + left-click and drag

### Useful Commands

Type these in the PyMOL console:

- `zoom` - Center and fit all objects in view
- `reset` - Reset the view to default
- `bg_color white` - Change background to white
- `bg_color black` - Change background to black
- `set transparency, 0.5` - Make surfaces semi-transparent
- `hide all` - Hide everything
- `show cartoon` - Show protein cartoon
- `show surface` - Show surfaces

### Object Panel (Right Side)

- Click object names to show/hide them
- Right-click for more options (color, style, etc.)
- Use the action buttons (A, S, H, L, C) for quick actions

## What Gets Loaded

Your PyMOL session automatically loads:

1. **Protein Structure** (if available)
   - Shown as cyan cartoon
   - Original PDB file

2. **Surface Files** (.ply)
   - **Red surfaces:** Target/binding sites
   - **Yellow surfaces:** Ligand surfaces
   - **Green surfaces:** Other molecular surfaces

3. **Optimized Settings**
   - White background
   - Anti-aliasing enabled
   - Nice rendering quality
   - Appropriate transparency

## Session Information

### Session Lifecycle

- **Creation:** New session created when you click "Visualize in PyMOL"
- **Duration:** Sessions expire after 1 hour of inactivity (configurable)
- **Cleanup:** Old sessions are automatically removed when you relaunch
- **Your Files:** Original result files are always safe and can be downloaded

### Session ID

Your session ID is shown at the top of the viewer. It looks like:
```
user123_job456_1234567890
```

This helps identify your session if you need support.

### Expiry Timer

The countdown timer shows how long until your session expires. When it expires:
- The PyMOL viewer will stop responding
- Simply click "Visualize in PyMOL" again to create a new session
- Your files are not affected

## Troubleshooting

### PyMOL Won't Load

**Check these:**
- Is your job status "COMPLETED"? (Visualization only works for completed jobs)
- Is PyMOL VDI enabled? (Contact admin if unsure)
- Try refreshing the page and clicking "Visualize in PyMOL" again

### Command Not Working

**Try these solutions:**
1. Use Tab autocomplete: Type `@/data/` then press `Tab`
2. Make sure you're typing in the PyMOL console (bottom window)
3. Check that your session folder appears when you press Tab
4. Verify the command starts with `@` (not just `/`)

### Results Don't Load

**Verify:**
- Did you press Enter after pasting the command?
- Is the command correct? It should start with `@/data/`
- Check the PyMOL console for error messages
- Try typing `ls /data/` to see if your session folder exists

### Viewer is Slow

**Optimize performance:**
- Reduce surface quality: `set surface_quality, 0`
- Hide some objects using the object panel
- Close other browser tabs
- Try a different browser (Chrome/Firefox recommended)

### Session Expired

**Solution:**
- Click "Close Viewer" button
- Click "Visualize in PyMOL" again
- A fresh session will be created

## Tips & Tricks

### Save Your View

To save a high-quality image:
```python
ray 2400, 2400
png my_image.png, dpi=300
```

### Custom Colors

Change object colors:
```python
color blue, protein
color red, surface_name
```

### Measure Distances

```python
distance dist1, /protein//A/123/CA, /protein//A/456/CA
```

### Select Residues

```python
select binding_site, resi 100-150
show sticks, binding_site
```

### Hide Water

```python
hide everything, resn HOH
```

## Advanced Features

### Loading Additional Files

If you have other files in your job directory:
```python
load /data/your_session_id/data/filename.pdb
```

### Custom Rendering

```python
set ray_trace_mode, 1
set ray_shadows, 1
set ambient, 0.4
set specular, 1
```

### Export Session

Save your PyMOL session:
```python
save /data/your_session_id/my_session.pse
```

## Getting Help

### In PyMOL

- Type `help` in the console for PyMOL help
- Type `help command_name` for specific command help
- Visit: https://pymolwiki.org/

### For This Interface

- Check the main Help page in the web interface
- Review the documentation in the job details page
- Contact: yewmun.yip@crick.ac.uk

## Best Practices

1. **Save your work:** Download result files before session expires
2. **Close when done:** Click "Close Viewer" to free up resources
3. **One session at a time:** Close old sessions before opening new ones
4. **Report issues:** Let us know if something doesn't work

## Keyboard Shortcuts

In PyMOL viewer:
- `Ctrl+Shift+V` - Paste
- `Ctrl+C` - Copy (in console)
- `Ctrl+L` - Clear console
- `Tab` - Autocomplete commands/paths

## FAQ

**Q: Can I use my local PyMOL instead?**
A: Yes! Download your result files and open them in your local PyMOL installation.

**Q: How long do sessions last?**
A: Default is 1 hour. The timer is shown in the viewer.

**Q: Can I share my session with others?**
A: No, sessions are private. Share result files instead.

**Q: What if I close the browser?**
A: Your session will remain active until it expires. You can return to the page and continue.

**Q: Can I run PyMOL scripts?**
A: Yes! Type `@/path/to/script.pml` or paste script commands in the console.

**Q: Why is there a delay when launching?**
A: Files are being downloaded from HPC and prepared for visualization. This is normal.

---

**Need more help?** Contact the Chemical Biology STP team at yewmun.yip@crick.ac.uk
