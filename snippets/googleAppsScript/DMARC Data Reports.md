## 🔍 Context

*This snippet finds, decompresses, and processes DMARC reports.*

DMARC (Domain-based Message Authentication, Reporting & Conformance) reports are XML files sent by email receivers (like Gmail or Yahoo) to domain owners, summarizing how their email messages performed against SPF and DKIM authentication checks. These reports help domain owners detect spoofing attempts, monitor legitimate sending sources, and fine-tune their domain’s email security policies.

## 🧠 Assumptions

1. The same Google account is being used for email, Sheets, and Apps Script
2. The associated Google Sheet has a sheet titled "Data" where data should be written.
3. DMARC reports are delivered to Gmail and labeled "DMARC"
   
## 💡 Snippet
```cpp
function processDMARCReports() {
  var threads = GmailApp.search('label:DMARC is:unread');
  if (threads.length === 0) {
    Logger.log('No DMARC threads found');
    return;
  }
  
  threads.forEach(function(thread) {
    thread.getMessages().forEach(function(msg) {
      var didProcess = false;
      msg.getAttachments().forEach(function(att) {
        if (!att.getName().match(/\.(gz|zip)$/)) return;
        
        Logger.log('Processing: ' + att.getName());
        var blobs;
        
        if (att.getName().endsWith('.gz')) {
          try {
            blobs = [ Utilities.ungzip(att) ];
          } catch(e1) {
            var raw     = att.getBytes();
            var wrapped = Utilities.newBlob(raw, 'application/x-gzip', att.getName());
            blobs = [ Utilities.ungzip(wrapped) ];
          }
        } else {
            if (att.getName().endsWith('.zip')) {
            var blobs;
            // Option A: try the attachment blob directly
            try {
              blobs = Utilities.unzip(att);
            }
            catch(e1) {
              // Option B: re‐wrap the raw bytes as a zip blob
              var raw = att.getBytes();
              var zipBlob = Utilities.newBlob(raw, 'application/zip', att.getName());
              blobs = Utilities.unzip(zipBlob);
            }
            blobs.forEach(processBlob);
          }
        }
        
        blobs.forEach(processBlob);
        didProcess = true;
      });
      if (didProcess) {
        msg.markRead();
        Logger.log('✅ Marked message as read: ' + msg.getSubject());
      }
    });
  });
}

function processBlob(blob) {
  // turn to string & parse
  var xmlText = blob.getDataAsString();
  var doc     = XmlService.parse(xmlText);
  var root    = doc.getRootElement();
  
  // --- extract metadata ---
  var meta       = root.getChild('report_metadata');
  var orgName    = meta.getChild('org_name').getText();
  var dr         = meta.getChild('date_range');
  var startEpoch = Number(dr.getChild('begin').getText());
  var endEpoch   = Number(dr.getChild('end').getText());
  
  // convert epochs → formatted dates
  var tz            = Session.getScriptTimeZone();
  var startDateStr  = Utilities.formatDate(new Date(startEpoch*1000), tz, "yyyy-MM-dd'T'HH:mm:ssZ");
  var endDateStr    = Utilities.formatDate(new Date(endEpoch*1000),   tz, "yyyy-MM-dd'T'HH:mm:ssZ");
  
  // pull records
  var records = root.getChildren('record');
  var sheet = SpreadsheetApp
               .getActiveSpreadsheet()
               .getSheetByName('Data');
  if (!sheet) {
    throw new Error('Sheet named "Data" not found');
  }
  
  // write header row if empty
  if (sheet.getLastRow() === 0) {
    sheet.appendRow([
      'Source IP','Count','SPF','DKIM','Disposition',
      'Start Date','End Date','Org Name'
    ]);
  }
  
  // append each record + metadata
  records.forEach(function(r){
    var row = r.getChild('row'),
        pol = row.getChild('policy_evaluated');
    sheet.appendRow([
      row.getChild('source_ip').getText(),
      row.getChild('count').getText(),
      pol.getChild('spf').getText(),
      pol.getChild('dkim').getText(),
      pol.getChild('disposition').getText(),
      startDateStr,
      endDateStr,
      orgName
    ]);
  });
}
```

## ⚠️ Notes & Gotchas

- This is only runs manually

## 🎟️ Future Updates

- Add to menu to run from the spreadsheet
- Run automatically every morning


## 🏷️ Tags
#googleSheets 
#googleAppsScript
#email