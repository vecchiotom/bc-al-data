using System;using System.Linq;using System.Reflection;using System.Collections;
var dir=Environment.GetEnvironmentVariable("AZ")!;
foreach(var f in System.IO.Directory.GetFiles(dir,"ALCops.*Cop.dll")){
 Assembly asm;try{asm=Assembly.LoadFrom(f);}catch{continue;}
 foreach(var t in asm.GetTypes()){
  foreach(var fi in t.GetFields(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Static)){
   if(!fi.FieldType.Name.Contains("DiagnosticDescriptor"))continue;
   object d;try{d=fi.GetValue(null)!;}catch{continue;} if(d==null)continue;
   string P(string n){var p=d.GetType().GetProperty(n);var v=p?.GetValue(d);return v==null?"":v.ToString()!.Replace("\t"," ").Replace("\n"," ");}
   Console.WriteLine($"{P("Id")}\t{P("DefaultSeverity")}\t{P("Category")}\t{P("IsEnabledByDefault")}\t{P("Title")}");
  }}}
