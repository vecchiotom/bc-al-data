// Every DiagnosticDescriptor from ALCops + Microsoft cop assemblies.
// Pass 1: static DiagnosticDescriptor fields on any type (ALCops style).
// Pass 2: SupportedDiagnostics of each instantiable DiagnosticAnalyzer (Microsoft style).
// AssemblyResolve redirects ALCops' pinned Microsoft.Dynamics.Nav.CodeAnalysis 18.0.36
// reference to whichever build sits in the compiler dir.
// Output: id<TAB>severity<TAB>category<TAB>enabledByDefault<TAB>title<TAB>messageFormat<TAB>assembly
using System;using System.Linq;using System.Reflection;using System.Collections;
var dirs=Environment.GetEnvironmentVariable("DIRS")!.Split(';');
AppDomain.CurrentDomain.AssemblyResolve+=(s,e)=>{
 var simple=new AssemblyName(e.Name).Name+".dll";
 foreach(var d in dirs){var p=System.IO.Path.Combine(d,simple);if(System.IO.File.Exists(p))return Assembly.LoadFrom(p);}
 return null;
};
var seen=new System.Collections.Generic.HashSet<string>();
void Emit(object d,string bn){
 if(d==null)return;var dt=d.GetType();if(dt.Name!="DiagnosticDescriptor")return;
 string P(string n){var p=dt.GetProperty(n);object v=null;try{v=p?.GetValue(d);}catch{}return v==null?"":v.ToString()!.Replace("\t"," ").Replace("\r"," ").Replace("\n"," ");}
 var id=P("Id");if(id==""||!seen.Add(id))return;
 Console.WriteLine($"{id}\t{P("DefaultSeverity")}\t{P("Category")}\t{P("IsEnabledByDefault")}\t{P("Title")}\t{P("MessageFormat")}\t{bn}");
}
foreach(var dir in dirs)foreach(var f in System.IO.Directory.GetFiles(dir,"*.dll")){
 var bn=System.IO.Path.GetFileName(f);
 if(!(bn.Contains("Cop")||bn.Contains("Analyzer")))continue;
 Assembly asm;try{asm=Assembly.LoadFrom(f);}catch{continue;}
 Type[] types;try{types=asm.GetTypes();}catch(ReflectionTypeLoadException e){types=e.Types.Where(t=>t!=null).ToArray()!;}catch{continue;}
 foreach(var t in types){
  if(t==null)continue;
  FieldInfo[] fields;try{fields=t.GetFields(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Static);}catch{fields=Array.Empty<FieldInfo>();}
  foreach(var fi in fields){
   string ftn;try{ftn=fi.FieldType.Name;}catch{continue;}
   if(ftn!="DiagnosticDescriptor")continue;
   try{Emit(fi.GetValue(null)!,bn);}catch{}
  }
  bool isAnalyzer;try{isAnalyzer=t.BaseType?.Name=="DiagnosticAnalyzer"||t.GetInterfaces().Any(i=>i.Name=="DiagnosticAnalyzer");}catch{isAnalyzer=false;}
  if(!isAnalyzer||t.IsAbstract||!t.IsClass)continue;
  object inst;try{inst=Activator.CreateInstance(t)!;}catch{continue;}
  var prop=t.GetProperty("SupportedDiagnostics");if(prop==null)continue;
  IEnumerable arr;try{arr=(IEnumerable)prop.GetValue(inst)!;}catch{continue;}
  foreach(var d in arr)try{Emit(d,bn);}catch{}
 }
}
