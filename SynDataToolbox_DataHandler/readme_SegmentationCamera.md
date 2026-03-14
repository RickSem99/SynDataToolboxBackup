# SegmentationCamera Plugin

## Unreal Editor setup

First of all, we need to set up MyActorHero's parameters in Unreal. We need to define the *base material* for the segmentation. Select from `Content/Materials` folder, into IsarPlugin, the **Segmentation_base_material**. Drag and drop it above the MyActorHero parameter. It's also necessary, for object dectection, to respect the label syntax for objects. All labels must be formatted like this: `ClassName_otherProperties`. The underscore is important because it used for parse Actor Labels.  

## Python setup

This plugin is classified as *Sensors* into IsarPlugin logic. The user-specified parameters are quite the same of RGBCamera: Width & Height of output masks, settings for video and images and so on. In addiction there are

- **object_to_find**: User can define which object classes are included into segmentation, defining class index as key (useful for output) and class name (to find into Unreal Engine level). Note that key 0 and value "other" are reserved and if they will be passed to the plugin, will be raised an exception.
- **format_output_mask**: User can choose the format for exporting mask. The possible choices are: ".png", ".csv", ".npy", ".mat".
- **channels**: as compared to "channels" parameter into RGBCamera sensor, the meaning is slighty different. In fact for this sensors channels define the type of mask: if `RGB` the output mask will be colorized, grayscale otherwise.

## IMPORTANT

1. At the moment, is important to respect a strict order into the list passed to `get_obs()` method: in fact the RGBCamera observation must be **always before** the SegmentationCamera observation. There's a weird bug into the plugin (cpp side) and we are working to find out.
2. At the moment, the plugin can classify at most 256 objects into unreal level.
