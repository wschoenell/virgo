RA 12:30:47 
DEC +12:20:13

ra, dec = 187.70, 12.34

1 - Radial search:
http://skyserver.sdss.org/dr7/en/tools/search/radial.asp

# Query 1 -- MyDB context
CREATE TABLE MyTable_34 (
 objid bigint,
 ra float,
 dec float,
 search_id int,
 matched_id bigint,
 z real
);

CREATE TABLE MyTable_32 (
 ra float,
 dec float,
 search_id int,
);

insert into MyDB.MyTable_32 values (187.70, 12.34, 1)

# Query 2 -- DR7 context
select top 0 * from specobj into MYDB.virgo

CREATE TABLE #UPLOAD(
 up_ra FLOAT,
 up_dec FLOAT,
 up_id int
)


INSERT INTO #UPLOAD
SELECT RA AS UP_RA,DEC AS UP_DEC,search_id AS UP_ID
FROM MYDB.MyTable_32

CREATE TABLE #tmp (
  up_id int,
  objid bigint
)

INSERT INTO #tmp
  EXEC spgetneighbors 480 -- 8 deg
  
INSERT INTO MYDB.virgo
select s.* 
from #tmp t 
  JOIN MYDB.MyTable_32 a ON t.up_id = a.search_id 
  JOIN specobj s ON s.bestobjid=t.objid


# Query 3 -- MyDB context
ALTER TABLE MYDB.virgo
DROP COLUMN img