# ComicTools
A set of tools for working with digital comics. Searching and tagging works best for individual issues, Volumes and TBPs tend not to return results when searching. Please use Comicvine if you are tagging a lot of comics. For small batches of recent comics, League of Comic Geeks is usually the fastest to update.

**Main Menu**

What would like to do? default: 1

* 1: Tag and organize.
* 2: Convert archive type.
* 3: Convert image type.
* 4: Remove scene promos.
* 5: Change Comic Database.
* 6: List Supported Archive Types.
* 7: Quit.

**Tag and organize**

Tag and organize allows you to select a single comic or a folder of comics to search for details. You will first confirm the series and then confirm the issue. Once confirmed, the file will be moved to the library folder with the naming convention in the config.

**Convert archive type**

Convert archive type allows you to select a single comic or a folder of comics to convert to another archive type. If the source file type is the same it will replace the exisitng. You can keep the original file by setting it in the config.

**Convert image type**

Convert image type allows you to select a single comic or a folder of comics to convert the images in the archive to. This process will replace the original file.

**Remove scene promos**

Remove scene promos allows you to select a single comic or a folder of comics to remove the scene promos in the archive. The are generally extra files added by scene groups that upload comics. This porcess will replace the original file.

**Change Comic Database**

This setting allows you to change the backend used to get comic details. The options are Comicvine,Comixology and League of Comic Geeks. The default is set in the config. **This change is only for runtime and will not be saved back to the config.**

**List Supported Archive Types**

This will list all archive types supported by your system. You will have to install the needed tools for the different archive types.



**Archive Types**

* CBZ - CBZ is natively supported by python.
* CBR - Extracting CBR will either need 7zip or unrar for extracting and WinRaR is needed for creating them.
* PDF - Extracting is supported natively in python through PyMuPDF and creating is handled natively in python Pillow.
* CB7 - Extracting and creating is handled by 7zip.
* CBA - Extracting is handled by 7zip and WinAce is needed for creating.
* CBT - Extracting and creating is handled native through python.
* EPUB - Extracting is handled native in python and creating is handled in python with Images_To_ePub. Thes are **very** simple epub files and may not be 100% compatible with all readers. If tagging, the name is set to the issue name and publisger is set to publisher. If just converting, the name is set to the file name and the publisher is set to ComicTools.

patool (https://wummel.github.io/patool/) - used for extracting and creating most archives.
Images_To_ePub (https://github.com/AVeenstra/Images_To_ePub) - used for creating epubs.

**Image Types**

* JPEG
* PNG
* WEBP
* BMP
* GIF
* TIFF

**config.json**

* remove_scene_promo - Removes scene promo images files from archive. The list of names is hard coded and if one isn't found, it will list potential ones that can be removed manually.
* remove_comixology_meta - The Comixology Backup Extension for Chrome (https://github.com/Cortys/comic-backup) adds a file to the archives to identify the person making the backup. This removes the file.
* remove_subfolders - This will remove any subfolders in the archive and move the files to the root.
* remove_hashed_files - This will remove files that match the sha256 hashes in the hashed_files list in the comictutil.json file.
* write_metadata - If set to true, metadata will be written to the folder if none exists. If set to false no metadata will be written. if set to overwrite, metadata will overwrite exisiting ones. If set to merge_existing, medata will be merged and exisitng entries will take prioroty. If set to merge_new, metadata will be mrged and new metadata will take priorty.
* library_location - Location of the library.
* keep_original - If set to true, selected file will be kept unless the source is same as target.
* compare_covers - Compare covers and give a % match for metadata cover to file cover.
* comicvine_key - Comicvine api key. This is needed for the comicvine backend.
* comic_database - This is the backend used to look for metadata details. The options are:
 locg - League of Comic Geeks (http://leagueofcomicgeeks.com/), comicvine - Comicvine (https://comicvine.gamespot.com/), and comixology - Comixology (https://www.comixology.com/)
 Comixology does not always give the start year for the series so the issue year is used for series year in that case
 * from_pdf_zoom - When extracting images from pdf, this is the resolution increase. If you are converting high quality pdfs, you can set this to 1.
 * archive_type - This is the archive type that will be used when tagging a comic with menu item 1. See archive types above for options. Set to lowercase.
 * metadata_type - The metadata format. Only Comicinfo.xml is supported. Comicapi from ComicTagger (https://github.com/comictagger/comictagger) is used for metadata support as well as some other naming functions.
 * image_type - The target image type used when tagging a comic. See above for supported types. Set to lowercase.
 * rename_template - This is the template used when renaming the comic. This will be appended to the library location. {seperator} is the file seperator for folders,{publisher} is publisher name, {series} is series name, {series_year} is the start year for the series, {issue_year} is year for the issue,{issue},{issue_pad2} and {issue_pad3} is the issue number. Setting the pad will padd the issue number with zeroes.

**The following will be used when tagging a comic and converting or just converting**:
* remove_scene_promo
* remove_comixology_meta
* remove_subfolders
* keep_original
* from_pdf_zoom
* image_type

```json
{
    "remove_scene_promo": true,
    "remove_comixology_meta": true,
    "remove_subfolders": true,
    "write_metadata": "merge_new",
    "library_location": "Y:\\Library",
    "keep_original": true,
    "compare_covers": true,
    "comicvine_key": "",
    "comic_database": "locg",
    "from_pdf_zoom": 4,
    "archive_type": "cbz",
    "metadata_type": "ComicInfo.xml",
    "image_type": "jpg",
    "rename_template": "{publisher}{seperator}{series} ({series_year}){seperator}{series} #{issue_pad3} ({issue_year})"
}
```

**comicdb.json**

This is used to keep the names from the different backend the same. Only publishers are supported. The value will replace the key if found.


```json
{
    "publishers": {
        "Marvel": "Marvel Comics",
        "DC": "DC Comics",
        "Image": "Image Comics",
        "Image - Skybound": "Skybound",
        "IDW Publishing": "IDW"
    }
}
```

**comicutil.json**

This is used to store the hashed_files,scene_promos and metadata files.


```json
{
    "scene_groups": [
        "zWater",
        "zzz-mephisto",
        "zSoU-Nerd",
        "zzoronewtag10",
        "zzoroboros",
        "zzzGlorithSolo",
        "ZZZZZ",
        "zzGGtag",
        "zDream",
        "zzorostnick11",
        "zEmpire-DrDoom",
        "zzzNeverAngel-Empire",
        "zzzDQzzz",
        "zzForsythe"
    ],
    "metadata_files": [
        "ComicInfo.xml",
        "ComicBookInfo.json",
        "CoMet.xml"
    ],
    "hashed_files": {
        "AFF3592205B673B198BDE35876DAC1D1541B5188931C325DF46B3F823A3F4887": "comixology presents.jpeg",
        "629B51E13107C44C9E73145FB357A65B39CCA7C38BE005B866EC2CC22397E0A7": "comixology presents.jpeg",
        "46C0228B7E8F1BC76A5F44F69A2AD98EADEEA4287ECBBC37EAD544E6E8E790E8": "comixology presents.jpeg"
    }
}
```
