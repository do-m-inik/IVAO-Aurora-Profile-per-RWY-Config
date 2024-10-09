# IVAO Aurora Profile per RWY Config
With this you can have a different profile per RWY Config

What this program can:
- Display different VORs, NDBs and FIXES per RWY Config
- Fill the active RWYs in Aurora depending on the RWY Config
- Fill the ATIS RWYs and Remarks depending on the RWY Config

It works for Germany if you have a german FIR sector file installed on Windows.

As example how to use a config, there is my currently used config for EDDH_APP on this repository.
You can also add different configs for different profiles.

The python prompt to use it on Windows:<br>
<code>python program.py --rwyconfig "[Config per RWY name]" --configfile "[Config file name].txt"</code>

There are also Batch files given which give you the possibility to just doubleclick it and then Aurora opens with the RWY configuration prefilled.

## Plans for the future:
- Filling in the TRL in the ATIS of the airport you control as APP or below
- Creating an exe, so you don't have to create separate config TXT files
- Recommend a RWY profile with the METAR of the current airport
- ...

### This is an unofficial project. There are no associations with the official Aurora from IVAO.

Official Website of IVAO: <code>[ivao.aero](https://ivao.aero)</code>

If you have any questions how to use the program or want to give feedback/suggestions:<br>
<code>mail@domi-schaefer.de</code>
