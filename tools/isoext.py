import pycdlib,sys,os
iso=pycdlib.PyCdlib();iso.open(sys.argv[1]);out=sys.argv[2]
for dp,ds,fs in iso.walk(iso_path='/'):
    for f in fs:
        p=dp+'/'+f if dp!='/' else '/'+f
        rec=iso.get_record(iso_path=p)
        dst=os.path.join(out,p.lstrip('/').split(';')[0]);os.makedirs(os.path.dirname(dst),exist_ok=True)
        iso.get_file_from_iso(dst,iso_path=p)
        print(rec.extent_location(),rec.get_data_length(),p)
