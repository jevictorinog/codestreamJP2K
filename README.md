# codestreamJP2K

The *struct.py* python script reads and analyzes the structure of a JPEG2000 file without the need to install any libraries.
To use *struct.py* provide the **filename** with the **path** of a valid JPEG2000 file

```python
python3 struct.py path/filename.jp2
```

## Access to image info selecting: 
* region (center_x, centery, width, height)
* reslution (integer)
* quality (integer)

This option receive JPEG2000 filename as input, and yielding a valid file JPEG2000 info requested

