#:package System.Collections.Immutable@10.0.0
using System;using System.Linq;using System.Reflection;
var dir=Environment.GetEnvironmentVariable("STORE")!;
var asm=Assembly.LoadFrom(System.IO.Path.Combine(dir,"Microsoft.Dynamics.Nav.CodeAnalysis.dll"));
var ec=asm.GetTypes().FirstOrDefault(t=>t.Name=="ErrorCode"&&t.IsEnum);
if(ec==null){Console.Error.WriteLine("no ErrorCode enum; candidate enums:");
 foreach(var t in asm.GetTypes().Where(t=>t.IsEnum&&t.Name.Contains("Code"))) Console.Error.WriteLine("  "+t.FullName);
 return;}
int n=0;
foreach(var name in Enum.GetNames(ec)){var v=(int)Enum.Parse(ec,name);Console.WriteLine($"AL{v:D4}\t{name}");n++;}
Console.Error.WriteLine($"{n} codes");
