// See https://aka.ms/new-console-template for more information
using client;

class Program
{
    static async Task Main(string[] args)
    {
        var listener = new ClientListener("http://localhost:5001/receive/");
        await listener.StartAsync(); 
    }
}