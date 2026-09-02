// Reflects the AL compiler's diagnostic message format strings.
// CompilerDiagnosticsResources is a RESX-backed ResourceManager whose keys are the
// exact ErrorCode enum names (ERR_/WRN_/INF_...). We read every key that matches an
// enum name and emit: AL####<TAB>enum_name<TAB>message_template  (tabs/newlines flattened).
using System;using System.Linq;using System.Reflection;using System.Resources;using System.Globalization;
var dir=Environment.GetEnvironmentVariable("STORE")!;
var asm=Assembly.LoadFrom(System.IO.Path.Combine(dir,"Microsoft.Dynamics.Nav.CodeAnalysis.dll"));
var ec=asm.GetTypes().First(t=>t.Name=="ErrorCode"&&t.IsEnum);
var resType=asm.GetTypes().First(t=>t.Name=="CompilerDiagnosticsResources");
var rm=(ResourceManager)resType.GetProperty("ResourceManager",BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Static)!.GetValue(null)!;
int n=0,hit=0;
foreach(var name in Enum.GetNames(ec)){
  var v=(int)Enum.Parse(ec,name);
  string msg="";
  try{msg=rm.GetString(name,CultureInfo.InvariantCulture)??"";}catch{}
  if(msg!="")hit++;
  msg=msg.Replace("\t"," ").Replace("\r"," ").Replace("\n"," ");
  Console.WriteLine($"AL{v:D4}\t{name}\t{msg}");
  n++;
}
Console.Error.WriteLine($"{n} codes, {hit} with message templates");
