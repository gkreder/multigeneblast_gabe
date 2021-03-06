#!/usr/bin/env python
## Copyright (c) 2012 Marnix H. Medema
## University of Groningen
## Department of Microbial Physiology / Groningen Bioinformatics Centre
## License: GNU General Public License v3 or later
## A copy of GNU GPL v3 should have been included in this software package in LICENSE.txt.

import os
import sys
from dblib.parse_gbk import parse_gbk_embl, fix_wgs_master_record, fix_supercontig_record
from dblib.utils import fasta_names, make_blast_db, clean_up, get_accession
from dblib.generate_genecords_tar import generate_genecords_tar
from dblib.generate_proteininfo_tar import generate_proteininfo_tar

#Find path to mgb files if run from another directory
pathfolders = os.environ['PATH'].split(os.pathsep)
pathfolders.append(os.getcwd())
pathfolders.append(os.getcwd().rpartition(os.sep)[0])
CURRENTDIR = os.getcwd()
MGBPATH = ""
for folder in pathfolders:
  try:
    if "read_input_gui.py" in os.listdir(folder) and "guilib.py" in os.listdir(folder) and "empty.xhtml" in os.listdir(folder) and "multigeneblast.py" in os.listdir(folder) and "mgb_gui.py" in os.listdir(folder):
      MGBPATH = folder
      break
  except:
    pass
if MGBPATH == "":
  print("Error: Please add the MultiGeneBlast installation directory to your $PATH environment variable before running the executable from another folder.")
  sys.exit(1)
#Set other environment variables
os.environ['EXEC'] = MGBPATH + os.sep + "exec"
os.environ['PATH'] = os.environ['EXEC'] + os.pathsep + os.environ['PATH']

def parse_options(args):
  #Parse options
  if len(args) < 2:
    print("""
    MAKEDB usage:
    
    Please specify database name and either one or more input files or a folder with input files.
    Usage for files: 'makedb dbname yourfile1.gbk yourfile2.gbk'
    Usage for folder: 'makedb dbname <folder name with input files>'
    """)
    sys.exit(1)
  dbname = args[0]
  overwrite = "y" #gkreder - hardcoded overwrite to 'yes'
  if dbname + ".nal" in os.listdir(".") or dbname + ".pal" in os.listdir("."):
    while overwrite != "y" and overwrite != "n":
      overwrite = input("Database with name exists in this folder. Overwrite? (y/n)")
    if overwrite == "n":
      sys.exit(1)
    if dbname + ".nal" in os.listdir("."):
        os.remove(dbname + ".nal")
    else:
        os.remove(dbname + ".pal")
  inputfiles = []
  for arg in [arg for arg in args if ".py" not in arg and "makedb" not in arg][1:]:
    root, ext = os.path.splitext(arg)
    if ext.lower() not in [".gbk",".gb",".genbank",".embl",".emb"]:
        if arg.rpartition(os.sep)[2] in os.listdir(".") or os.path.exists(arg) or os.path.exists(os.getcwd() + os.sep + arg):
          try:
            os.chdir(arg.rpartition(os.sep)[2])
          except:
            try:
              os.chdir(arg)
            except:
              try:
                os.chdir(os.getcwd() + os.sep + arg)
              except:
                print("Error: cannot open folder", arg.rpartition(os.sep)[2], "or file does not have GBK/EMBL/FASTA extension")
                sys.exit()
          filesfound = "n"
          for filename in os.listdir("."):
            root, fext = os.path.splitext(filename)
            if fext.lower() in [".gbk",".gb",".genbank",".embl",".emb"]:
              # inputfiles.append(arg.rpartition(os.sep)[0] + os.sep + filename)
              inputfiles.append(os.path.join(arg, filename)) #gkreder - this top line wasn't working...
              filesfound = "y"
          if filesfound == "n":
            print("Error: no GBK/EMBL files found in folder", arg)
            sys.exit(1)
          os.chdir("..")
        else:
          print("Please supply input file with valid GBK / EMBL extension.")
          sys.exit(1)
    elif arg in os.listdir(".") or (os.sep in arg and arg.rpartition(os.sep)[2] in os.listdir(arg.rpartition(os.sep)[0])):
        inputfiles.append(arg)
    else:
        print("Error: specified input file", arg , "not found.")
        sys.exit(1)


  return inputfiles, dbname

def main():
  global GUI
  GUI = "n"
  top_dir = os.getcwd()
  args = sys.argv
  if "makedb" in args[0]:
    args = args[1:]
  inputfiles, dbname = parse_options(args)
  inputfiles = [os.path.abspath(os.path.join(top_dir, x)) for x in inputfiles] #gkreder
  logfile = open("makedb.log","w")

  #Create FASTA database
  print("Creating FASTA file")
  descriptions = parse_gbk_embl(inputfiles, dbname)

  #Create Blast database
  print("Constructing Blast+ database")
  os.system("makeblastdb -dbtype prot -out " + dbname + " -in " + dbname + "_dbbuild.fasta")

  #Create genbank_mf_all.txt file
  print("Generating _all.txt file")
  fasta_names(dbname + "_dbbuild.fasta", dbname + "_all.txt")

  #Create genbank_mf_all_descrs.txt file
  print("Generating " + dbname + "_all_descr.txt file")
  descrfile = open(dbname + "_all_descrs.txt","w")
  descrkeys = list(descriptions.keys())
  descrkeys.sort()
  for key in descrkeys:
    descrfile.write(key + "\t" + descriptions[key] + "\n")
  descrfile.close()

  #Create Blast database and TAR archives
  if "\n" not in open(dbname + "_dbbuild.fasta","r").read():
    print("Error making BLAST database; no suitable sequences found in input.")
    clean_up(dbname, top_dir)
    sys.exit()
  make_blast_db(dbname, dbname + "_dbbuild.fasta")
  generate_genecords_tar(dbname)
  generate_proteininfo_tar(dbname)
  
  #Clean up
  clean_up(dbname, top_dir)

if __name__ == "__main__":
  main()
